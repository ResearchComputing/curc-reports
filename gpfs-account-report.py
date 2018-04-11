#!/usr/bin/env python

import argparse
import csv
import datetime
import os
import re
import subprocess


BASE_TABLE_F = "{project:<28}{block_used:>11}{block_limit:>11}"

FILES_F = "{files_used:>11}{files_limit:>11}"

OCCUPANCY_P = re.compile(r'^.* TOTAL FILESET - RESIDENT:[0-9]+ MIGRATED:[0-9]+ PREMIGRATED:[0-9]+ TOTAL_MB:([0-9]+) DISK_MB:([0-9]+)$')


def main ():
    parser = argparse.ArgumentParser()
    parser.add_argument('projects', nargs='+')
    parser.add_argument('--quota-file')
    parser.add_argument('--gpfs-device')
    parser.add_argument('--show-files', action='store_true', default=False)
    parser.add_argument('--output-csv')
    args = parser.parse_args()

    current_date = datetime.date.today()

    if args.quota_file:
        quota_from_file = parse_quota_file(args.quota_file)
    else:
        quota_from_file = None

    if args.gpfs_device:
        gpfs_quota = dict(
            (item['name'], item)
            for item in mmrepquota(args.gpfs_device)
        )
    else:
        gpfs_quota = None

    print "# {current_date} usage report for PetaLibrary/archive".format(current_date=current_date)

    table_f = BASE_TABLE_F
    if args.show_files:
        table_f += FILES_F

    header = dict(
        project = 'Project',
        block_used = 'BlockUsed',
        block_limit = 'BlockLimit',
        files_used = 'FilesUsed',
        files_limit = 'FilesLimit',
    )

    print table_f.format(**header)

    if args.output_csv:
        csv_writer = csv.DictWriter(
            open(args.output_csv, 'wb'),
            ('project', 'block_used', 'block_limit', 'files_used', 'files_limit'),
        )
        csv_writer.writerow(header)
    else:
        csv_writer = None

    for project in args.projects:
        if gpfs_quota:
            block_used_mib = 1.0 * gpfs_quota[project]['blockUsage'] / 1024
            files_used = gpfs_quota[project]['filesUsage']
            files_limit = gpfs_quota[project]['filesLimit']
        else:
            block_used_mib, _ = read_occupancy_file('/archive', project)
            files_used = 0
            files_limit = 0

        if quota_from_file:
            block_limit_tb = quota_from_file.get(project, 'unknown')
        elif gpfs_quota:
            block_limit_tb = mib_to_tb(1.0 * gpfs_quota[project]['blockLimit'] / 1024)
        else:
            block_limit_tb = 0

        block_used_tb = mib_to_tb(block_used_mib)

        values = dict(
            project = project,
            block_used = '{0:.1f}'.format(block_used_tb),
            block_limit = '{0:.1f}'.format(block_limit_tb),
            files_used = files_used,
            files_limit = files_limit,
        )

        print table_f.format(**values)

        if csv_writer:
            csv_writer.writerow(values)


def read_occupancy_file (fs_path, project):
    try:
        with open(os.path.join(fs_path, project, 'occupancy.log')) as fp:
            for line in fp:
                match = OCCUPANCY_P.match(line)
                if match:
                    total_mib, disk_mib = match.groups()
    except IOError:
	return 0, 0
    else:
        return int(total_mib), int(disk_mib)


def parse_quota_file (quota_file):
    quota = {}
    with open(quota_file) as fp:
        for line in fp:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            else:
                project, quota_value = line.split()
                quota[project] = int(quota_value)
    return quota


def mmrepquota (gpfs_device):
    cmd = ['/usr/lpp/mmfs/bin/mmrepquota', '-Y', '-j', gpfs_device]
    header = None
    mmrepquota_ = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = mmrepquota_.communicate()
    for line in stdout.splitlines():
        fields = line.split(':')
        if not fields[0] == 'mmrepquota':
            continue
        elif header is None:
            header = fields
        else:
            item = dict(zip(header, fields))
            for field in ('blockUsage', 'blockLimit', 'filesUsage', 'filesLimit'):
                if field in item:
                    item[field] = int(item[field])
            yield item
    


def mib_to_tb (mib):
    return 1.0 * mib * (1024 ** 2) / (1000 ** 4)


if __name__ == '__main__':
    main()

