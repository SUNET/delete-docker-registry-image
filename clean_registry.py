#!/usr/bin/env python

import re
import sys
import json
import subprocess
import requests
import yaml
import ipaddress
import clean_old_versions

# Nagios plugin exit status codes
STATUS = {'OK': 0,
          'WARNING': 1,
          'CRITICAL': 2,
          'UNKNOWN': 3,
         }

def get_container_ip(container_name):
    process = subprocess.Popen(['/usr/bin/docker', 'inspect', 
            '--format=\'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}\'',
            container_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    returncode = process.wait()

    if returncode != 0:
        print("Could not get IP address of the registry container")
        sys.exit(STATUS['CRITICAL'])

    # Read the output and remove \n
    container_ip = process.stdout.read().rstrip()

    # The output needs cleaning since it
    # contains superfluous quotation marks.
    container_ip = container_ip.strip('\"\'')

    try:
        # This backported module requires that the
        # argument is a unicode object.
        ipaddress.ip_address(container_ip.decode("UTF-8"))
    except ValueError:
        print("Did not get a properly formatted IP address for the registry container")
        sys.exit(STATUS['CRITICAL'])

    return container_ip

def clean(config):

    for image_to_clean in config['exact_images']:
        registry_catalog = clean_old_versions.get_catalog(parse_args(config))

        for image_in_registry in registry_catalog:
            if image_to_clean == image_in_registry:
                image_config = config['exact_images'][image_to_clean]
                args = parse_args(config=config, image=image_to_clean,
                        exclude = image_config['regex_of_tags_to_save'],
                        include = image_config['regex_of_tags_to_delete'],
                        last = image_config['number_of_latest_builds_to_save'])
                print("Starting cleanup of image: {}".format(image_to_clean))
                clean_old_versions.delete_matching_tags(registry_catalog, args)

    for group in config['group_images']:
        registry_catalog = clean_old_versions.get_catalog(parse_args(config))

        for image_in_registry in registry_catalog:
            if re.match(group, image_in_registry):
                group_config = config['group_images'][group]
                args = parse_args(config=config, image=image_in_registry,
                        exclude=group_config['regex_of_tags_to_save'],
                        include=group_config['regex_of_tags_to_delete'],
                        last=group_config['number_of_latest_builds_to_save'])
                print("Starting cleanup of image: {}".format(image_in_registry))
                clean_old_versions.delete_matching_tags(registry_catalog, args)

def parse_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config

def parse_args(config, image=None, exclude=None, include=None, last=None):
    args = clean_old_versions.get_arguments(require_arguments=False)

    if config['registry_url']:
        args.registry_url = config['registry_url']
    else:
        args.registry_url = "http://{}:{}".format(get_container_ip(config['registry_container_name']),
                                                  config['registry_container_port'])

    args.registry_data_dir = config['registry_data_dir']
    args.script_path = config['delete_docker_registry_image_path']
    args.image = image
    args.exclude = exclude
    args.include = include
    args.last = last

    return args

def main():

    if len(sys.argv) != 2:
        print('Usage: clean_registry.py config_file.yaml')
        sys.exit(STATUS['WARNING'])

    config_file = sys.argv[1]

    # Remove arguments since otherwise they are read by
    # clean_old_versions.py that doesn't recognize our arguments.
    sys.argv = [sys.argv[0]]

    config = parse_config(config_file)
    clean(config)
    sys.exit(STATUS['OK'])

if __name__ == "__main__":
    main()
