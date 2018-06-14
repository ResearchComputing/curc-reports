#!/usr/bin/env python


import argparse
import csv
import datetime
import email.mime.text
import logging
import os
import pwd
import smtplib
import subprocess
import sys


REPORT_HEADER = """This is an automated cluster account activity report.

This report has recently been rewritten. Please share your feedback
with rc-help@colorado.edu.

Cluster(s): {clusters}
Report period: {starttime} to {endtime}"""


ACCOUNT_HEADER = """

## Account: {account}
"""

ACCOUNT_SHARE = """Current share utilization: {share_usage:,.0%} (as of {current_time})
"""

ACCOUNT_BODY = """Number of jobs run: {jobs:,}
Core-hours used: {core_hours:,.0f}
Median queue wait time: {median_wait_time}
Median runtime: {median_runtime}
"""

USER_HEADER = """The following users are authorized to run jobs in {account}. The
number of core-hours used by each is listed in parentheses.
"""

USER_LINE = "* {username} - {given_name} ({core_hours:,.0f})"

NO_USERS = "*No authorized users*"

REPORT_FOOTER = """

Please contact rc-help@colorado.edu if you have any questions or
concerns."""


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parser ():
    parser = argparse.ArgumentParser(description="Generate activity reports for Slurm accounts.")
    parser.add_argument('accounts', nargs='*', help="List of slurm accounts to include in report")
    parser.add_argument('-s', '--starttime', metavar='TIME_STRING', default=last_month().strftime('%Y-%m-%d'), help="Reporting period start time as Slurm TIME_STRING. Default: the start of the previous month.")
    parser.add_argument('-e', '--endtime', metavar='TIME_STRING', default=this_month().strftime('%Y-%m-%d'), help="Reporting period end time as Slurm TIME_STRING. Default: the start of the current month.")
    parser.add_argument('-M', '--clusters', help="Comma-separated list of clusters to include in report")
    parser.add_argument('--email', metavar="ADDRESS", help="Send report to ADDRESS")
    parser.add_argument('--batch', metavar="CSV", help="Read accounts, clusters, and email addresses from CSV")
    parser.add_argument('--no-fairshare', action='store_true', default=False, help="Do not include fairshare information in report")
    parser.add_argument('--quiet', action='store_true', default=False, help="Suppress logging of non-critical events to console")
    parser.add_argument('--verbose', action='store_true', default=False, help="Log informational events to console")
    parser.add_argument('--debug', action='store_true', default=False, help="Log debug events to console")
    parser.add_argument('--noop', action='store_true', default=False, help="Do not send reports via email, even when email addresses are provided")
    return parser


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

    if args.batch and args.accounts:
        exit_with_msg('Cannot specify accounts when running in batch mode')

    if args.batch:
        with open(args.batch, 'rb') as fp:
            reader = csv.reader(fp)
            for recipients, clusters, accounts in reader:
                if args.email:
                    recipients_ = args.email.split(',')
                else:
                    recipients_ = recipients.split(',')
                report = build_report(
                    clusters=args.clusters or clusters,
                    starttime=args.starttime,
                    endtime=args.endtime,
                    accounts=accounts.split(','),
                    fairshare=not args.no_fairshare,
                )
                send_email(
                    recipients_,
                    report,
                    starttime=args.starttime,
                    endtime=args.endtime,
                    clusters=args.clusters or clusters,
                    noop=args.noop,
                )
    else:
        report = build_report(
            clusters=args.clusters,
            starttime=args.starttime,
            endtime=args.endtime,
            accounts=args.accounts,
            fairshare=not args.no_fairshare,
        )
        if args.email:
            send_email(
                args.email.split(','),
                report,
                starttime=args.starttime,
                endtime=args.endtime,
                clusters=args.clusters,
                noop=args.noop,
            )
        else:
            print report


def last_month ():
    last_month = (this_month() - datetime.timedelta(days=1))
    return datetime.date(year=last_month.year, month=last_month.month, day=1)


def this_month ():
    today = datetime.date.today()
    return datetime.date(year=today.year, month=today.month, day=1)


def build_report (clusters=None, starttime=None, endtime=None, accounts=None, fairshare=True):
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

        core_hours = seconds_to_hours(sum(record['CPUTimeRAW'] for record in records))
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
                seconds_to_hours(sum(record['CPUTimeRAW'] for record in records if record['User'] == user)),
            )
            for user in account_users
        ]

        report.append(ACCOUNT_HEADER.format(
            account=account,
        ))

        if fairshare:
            share_info = [
                record for record in sshare(
                    accounts=account,
                    clusters=clusters,
                )
                if not record['User']
            ][0]
            share_usage = share_info['EffectvUsage'] / share_info['NormShares']
            report.append(ACCOUNT_SHARE.format(
                share_usage=share_usage,
                current_time=datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            ))

        report.append(ACCOUNT_BODY.format(
            jobs=len(records),
            core_hours=core_hours,
            median_wait_time=median_wait_time,
            median_runtime=median_runtime,
        ))

        report.append(USER_HEADER.format(
            account=account,
        ))

        user_lines = [
            USER_LINE.format(
                username=username,
                given_name=given_name(username),
                core_hours=core_hours,
            )
            for username, core_hours in sorted(user_info, key=lambda t: t[1], reverse=True)
        ]

        if user_lines:
            report.extend(user_lines)
        else:
            report.append(NO_USERS)

    report.append(REPORT_FOOTER)

    return os.linesep.join(report)


def send_email (recipients, report, starttime, endtime, clusters, noop=False):
    logger.info('sending report to {}'.format(', '.join(recipients)))

    msg = email.mime.text.MIMEText(report)
    msg['Subject'] = "Cluster account activity report: {starttime} to {endtime} for {clusters}".format(
        starttime=starttime,
        endtime=endtime,
        clusters=clusters,
    )
    msg['From'] = "slurm@rc.colorado.edu"
    msg['Reply-To'] = "rc-help@colorado.edu"
    msg['To'] = ', '.join(recipients)

    if not noop:
        s = smtplib.SMTP('localhost')
        s.sendmail(msg['From'], recipients, msg.as_string())
        s.quit()


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


def sshare (accounts=None, clusters=None):
    cmd = ['/usr/bin/sshare', '--parsable2', '--all']
    if accounts:
        cmd.extend(('--accounts', accounts))
    if clusters:
        cmd.extend(('--clusters', clusters))

    logger.debug(' '.join(cmd))
    sshare_p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sshare_p.communicate()

    if sshare_p.returncode != 0 or stderr:
        raise Exception(stderr)

    lines = [ # FIXME
        line for line in stdout.splitlines()
        if line.strip() and not line.startswith('CLUSTER: ')
    ]

    header = lines[0].rstrip().split('|')
    for line in lines[1:]:
        line = line.rstrip().split('|')
        record = dict(zip(header, line))
        for integer_field in ('RawShares', 'RawUsage'):
            if integer_field in record:
                try:
                    record[integer_field] = int(record[integer_field])
                except ValueError:
                    pass
        for float_field in ('NormShares', 'EffectvUsage', 'FairShare'):
            if float_field in record:
                try:
                    record[float_field] = float(record[float_field])
                except ValueError:
                    pass
        for none_field in ('User', ):
            if none_field in record and not record[none_field]:
                record[none_field] = None
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


def given_name (username):
    try:
        return pwd.getpwnam(username).pw_gecos.split(',')[0]
    except KeyError:
        return "(unknown)"


def exit_with_msg(err_msg, ex=None, exit_code=1):
    if ex:
        err_msg_ts = '{}\n{}'.format(err_msg, ex)
    else:
        err_msg_ts = '{}'.format(err_msg)
    logger.critical(err_msg_ts)
    sys.exit(exit_code)


def seconds_to_hours (seconds):
    return 1.0 * seconds / 60 / 60


if __name__ == '__main__':
    main()
