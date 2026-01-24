#!/usr/bin/env python3
# Copyright (c) 2019 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
"""
Download all blobs defined in blobs.yaml
"""
import os
import sys
import yaml
import subprocess
import hashlib
import shutil
from argparse import ArgumentParser


    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_blobs(top_dir, blobs_yaml, cache_dir, dist_base):
    """Download all blobs from the distribution server."""
    with open(blobs_yaml, 'r') as f:
        blobs = yaml.safe_load(f)

    total = len(blobs)
    downloaded = 0
    skipped = 0
    failed = 0

    for i, blob in enumerate(blobs, 1):
        dest = blob['dest'].lstrip('/')
        source = blob['source']
        shasum = blob['shasum']
        size = blob['size']

        dest_path = os.path.join(top_dir, dest)
        cache_path = os.path.join(cache_dir, source)

        print(f'[{i}/{total}] {dest}')

        # Check if file already exists with correct hash
        if os.path.exists(dest_path):
            file_hash = calculate_sha256(dest_path)
            if file_hash == shasum:
                print(f'  Already exists with correct hash, skipping')
                skipped += 1
                continue

        # Create destination directory
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Check cache
        if os.path.exists(cache_path):
            file_hash = calculate_sha256(cache_path)
            if file_hash == shasum:
                print(f'  Using cached file')
                shutil.copy2(cache_path, dest_path)
                downloaded += 1
                continue

        # Download from distribution server
        url = f'{dist_base}/{source}'
        print(f'  Downloading from {url}')
        result = subprocess.run(
            ['curl', '-fsSL', '--retry', '5', '-o', dest_path, url],
            capture_output=True
        )
        if result.returncode != 0:
            print(f'  FAILED to download: {result.stderr.decode()}')
            failed += 1
            continue

        # Verify checksum
        file_hash = calculate_sha256(dest_path)
        if file_hash != shasum:
            print(f'  CHECKSUM MISMATCH! Expected {shasum}, got {file_hash}')
            os.remove(dest_path)
            failed += 1
            continue

        # Cache the file
        os.makedirs(cache_dir, exist_ok=True)
        shutil.copy2(dest_path, cache_path)

        downloaded += 1

    print(f'\nSummary: {downloaded} downloaded, {skipped} skipped, {failed} failed out of {total} blobs')
    return failed == 0


def main():
    parser = ArgumentParser(description='Download all blobs defined in blobs.yaml')
    parser.add_argument('-t', '--top', required=True, help='Top directory of the repo')
    parser.add_argument('-b', '--blobs-yaml', required=True, help='Path to blobs.yaml')
    parser.add_argument('-c', '--cache', required=True, help='Cache directory')
    parser.add_argument('-d', '--dist', required=True, help='Distribution server URL')
    args = parser.parse_args()

    success = download_blobs(args.top, args.blobs_yaml, args.cache, args.dist)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

