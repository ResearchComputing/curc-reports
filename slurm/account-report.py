#!/usr/bin/env python


import argparse
import datetime
import logging
import os
import pwd
import subprocess


REPORT_HEADER = """This is an automated cluster account activity report.

Cluster(s): {clusters}
Report period: {starttime} to {endtime}."""


REPORT_BODY = """## Account: {account}

Total number of jobs run: {jobs:,}
Total core-hours used: {core_hours:,.0f} 
Median queue wait time: {median_wait_time}
Median runtime: {median_runtime}

The following users are authorized to run jobs in {account}. The
number of core-hours used by each is listed in parentheses.

{user_report}"""


USER_T = "* {username:<10} {given_name} ({core_hours:,.0f})"


REPORT_FOOTER = """Please contact rc-help@colorado.edu if you have any questions or
concerns."""


# subject: "Blanca Usage Report ${MONTH} ${Y}\" -S from=slurm@rc.colorado.edu -S replyto=rc-help@colorado.edu -b jonathon.anderson@colorado.edu ${EMAIL}"


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def main ():
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(asctime)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    logger.addHandler(console_handler)
    
    args = parser().parse_args()

    if args.quiet and args.verbose:
        exit_with_msg('Cannot be both verbose and quiet')
    elif args.quiet and args.debug:
        exit_with_msg('Cannot be both quiet and debug')
    else:
        if args.quiet:
            console_handler.setLevel(logging.CRITICAL)
        elif args.verbose or args.debug:
            if args.debug:
                console_handler.setLevel(logging.DEBUG)
            else:
                console_handler.setLevel(logging.INFO)
        
        else:
            console_handler.setLevel(logging.WARNING)

    print build_report(
        clusters=args.clusters,
        starttime=args.starttime,
        endtime=args.endtime,
        accounts=args.accounts,
    )


def build_report (clusters=None, starttime=None, endtime=None, accounts=None):
    report = []
    report.append(REPORT_HEADER.format(
        clusters=clusters or "unspecified",
        starttime=starttime,
        endtime=endtime,
    ))

    for account in accounts:
        records = list(sacct(
            format_='Submit,Start,End,User,CPUTimeRAW',
            starttime=starttime,
            endtime=endtime,
            accounts=account,
            clusters=clusters,
        ))

        core_hours = 1.0 * sum(record['CPUTimeRAW'] for record in records) / 60
        median_wait_time = median_timedelta([record['Start'] - record['Submit'] for record in records if record['Submit'] is not None and record['Start'] is not None])
        median_runtime = median_timedelta([record['End'] - record['Start'] for record in records if record['Start'] is not None and record['End'] is not None])

        account_users = set(
            association['User']
            for association in sacctmgr(('list', 'associations'), clusters=clusters, accounts=account)
            if association['User']
        )

        user_info = [
            (
                user,
                1.0 * sum(record['CPUTimeRAW'] for record in records if record['User'] == user) / 60,
            )
            for user in account_users
        ]

        user_report = os.linesep.join(
            USER_T.format(
                username=username,
                given_name=pwd.getpwnam(username).pw_gecos.split(',')[0],
                core_hours=core_hours,
            )
            for username, core_hours in sorted(user_info, key=lambda t: t[1], reverse=True)
        )


        report.append(REPORT_BODY.format(
            account=account,
            jobs=len(records),
            core_hours=core_hours,
            median_wait_time=median_wait_time,
            median_runtime=median_runtime,
            user_report=user_report,
        ))

    report.append(REPORT_FOOTER)

    return (os.linesep * 3).join(report)


def parser ():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--starttime', default=datetime.date.today().strftime('%Y-%m-%d'))
    parser.add_argument('-e', '--endtime', default=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    parser.add_argument('-M', '--clusters')
    parser.add_argument('--email')
    parser.add_argument('accounts', nargs='*')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument('--debug', action='store_true')
    return parser


def sacct (truncate=True, allocations=True, starttime=None,
           endtime=None, accounts=None, format_=None, clusters=None):
    cmd = ['/usr/bin/sacct', '--parsable2', '--allusers']
    if truncate:
        cmd.append('--truncate')
    if allocations:
        cmd.append('--allocations')
    if starttime:
        cmd.extend(('--starttime', starttime))
    if endtime:
        cmd.extend(('--endtime', endtime))
    if accounts:
        cmd.extend(('--accounts', accounts))
    if format_:
        cmd.extend(('--format', format_))
    if clusters:
        cmd.extend(('--clusters', clusters))

    logger.debug(' '.join(cmd))
    sacct_p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sacct_p.communicate()

    if sacct_p.returncode != 0 or stderr:
        raise Exception(stderr)

    lines = stdout.splitlines()

    header = lines[0].rstrip().split('|')

    for line in lines[1:]:
        line = line.rstrip().split('|')
        record = dict(zip(header, line))
        if 'CPUTimeRAW' in record:
            record['CPUTimeRAW'] = int(record['CPUTimeRAW'])
        for date_field in ('Submit', 'Start', 'End'):
            if date_field in record:
                try:
                    record[date_field] = datetime.datetime.strptime(record[date_field], '%Y-%m-%dT%H:%M:%S')
                except ValueError:
                    record[date_field] = None
        yield record


def sacctmgr (subcommand, accounts=None, clusters=None):
    cmd = ['/usr/bin/sacctmgr', '--parsable2', '--immediate']
    cmd.extend(subcommand)
    if accounts:
        cmd.append('Accounts={}'.format(accounts))
    if clusters:
        cmd.append('Clusters={}'.format(clusters))

    logger.debug(' '.join(cmd))
    sacct_p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sacct_p.communicate()

    if sacct_p.returncode != 0 or stderr:
        raise Exception(stderr)

    lines = stdout.splitlines()

    header = lines[0].rstrip().split('|')

    for line in lines[1:]:
        line = line.rstrip().split('|')
        record = dict(zip(header, line))
        yield record


def median_timedelta (list_):
    sorted_list = sorted(list_)
    length = len(sorted_list)
    center = length // 2

    if length == 1:
        return sorted_list[0]

    elif length % 2 == 0:
        return sum(sorted_list[center - 1: center + 1], datetime.timedelta(0)) / 2

    else:
        return sorted_list[center]


if __name__ == '__main__':
    main()
