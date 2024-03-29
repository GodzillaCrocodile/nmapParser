# EStroev
# !/usr/bin/env python


__description__ = 'nmap xml script output parser'
__author__ = 'Didier Stevens, modify by Sumedt Jitpukdebodin'
__version__ = '0.2'
__date__ = '2014/04/30'

import optparse
import xml.dom.minidom
import glob
import collections

QUOTE = '"'


def ToString(value):
    if type(value) == type(''):
        return value
    else:
        return str(value)


def Quote(value, separator, quote):
    value = ToString(value)
    if separator in value:
        return quote + value + quote
    else:
        return value


def MakeCSVLine(row, separator, quote):
    return separator.join([Quote(value, separator, quote) for value in row])


class cOutput():
    def __init__(self, filename=None):
        self.filename = filename
        if self.filename and self.filename != '':
            self.f = open(self.filename, 'w')
        else:
            self.f = None

    def Line(self, line):
        if self.f:
            self.f.write(line + '\n')
        else:
            print(line)

    def Close(self):
        if self.f:
            self.f.close()
            self.f = None


class cOutputCSV():
    def __init__(self, options):
        if options.output:
            self.oOutput = cOutput(options.output)
        else:
            self.oOutput = cOutput()
        self.options = options

    def Row(self, row):
        self.oOutput.Line(MakeCSVLine(row, self.options.separator, QUOTE))

    def Close(self):
        self.oOutput.Close()


def NmapXmlParser(filenames, options):
    oOuput = cOutputCSV(options)
    oOuput.Row(
        ['IP', 'Hostname', 'Port', 'Service', 'Product', 'OS'])
    for filename in filenames:
        domNmap = xml.dom.minidom.parse(open(filename, 'r'))

        #### Add date
        nmap_header = domNmap.getElementsByTagName('nmaprun')

        #### Add end date
        nmap_footer = domNmap.getElementsByTagName('runstats')

        for hosttag in domNmap.getElementsByTagName('host'):
            ostype = ''
            for port in hosttag.getElementsByTagName('port'):
                for service in port.getElementsByTagName('service'):
                    portName = service.getAttribute('name')
                    if portName == 'microsoft-ds':
                        ostype = service.getAttribute('product').strip(' microsoft-ds')

            for port in hosttag.getElementsByTagName('port'):
                scriptFound = False
                row = list()

                addresses = [address.getAttribute('addr') for address in hosttag.getElementsByTagName('address') if
                             address.getAttribute('addrtype') == 'ipv4']

                row.append('|'.join(addresses))
                vendors = [address.getAttribute('vendor') for address in hosttag.getElementsByTagName('address') if
                           address.getAttribute('addrtype') == 'mac']
                # row.append('|'.join(vendors))
                ### Remove all hostname(user,ptr) to be just user type only.
                # hostnames = [hostname.getAttribute('name') for hostname in hosttag.getElementsByTagName('hostname')]
                hostnames = [hostname.getAttribute('name') for hostname in
                             hosttag.getElementsByTagName('hostname')]  # if hostname.getAttribute('type') == 'user']
                row.append('|'.join(hostnames))
                row.append(port.getAttribute('portid'))

                # for state in port.getElementsByTagName('state'):
                #     row.append(state.getAttribute('state'))

                for service in port.getElementsByTagName('service'):
                    row.append(service.getAttribute('name'))
                    row.append(service.getAttribute('product'))
                    if not ostype:
                        ostype = service.getAttribute('ostype')
                    if ostype == 'IOS':
                        ostype = 'Cisco IOS'
                    elif ostype == 'VRP':
                        ostype = 'Huawei VRP'
                    elif ostype == 'AOS':
                        ostype = 'APC AOS'
                    row.append(ostype)

                    # print(addresses, port.getAttribute('portid'), ostype)
                print(row)
                # print(row)
        # if hosttag.getElementsByTagName('script'):
        # scriptFound = True
        # for script in hosttag.getElementsByTagName('script'):
        #     row.append(script.getAttribute('id'))
        #     row.append(repr(script.getAttribute('output').encode('ascii').replace('\n  ','')))
                oOuput.Row(row)


    oOuput.Close()


def File2Strings(filename):
    try:
        f = open(filename, 'r')
    except:
        return None
    try:
        return map(lambda line: line.rstrip('\n'), f.readlines())
    except:
        return None
    finally:
        f.close()


def ProcessAt(argument):
    if argument.startswith('@'):
        strings = File2Strings(argument[1:])
        if strings == None:
            raise Exception('Error reading %s' % argument)
        else:
            return strings
    else:
        return [argument]


def ExpandFilenameArguments(filenames):
    return list(collections.OrderedDict.fromkeys(sum(map(glob.glob, sum(map(ProcessAt, filenames), [])), [])))


def Main():
    moredesc = '''

Arguments:
@file: process each file listed in the text file specified
wildcards are supported'''

    oParser = optparse.OptionParser(usage='usage: %prog [options] [@]file ...\n' + __description__ + moredesc,
                                    version='%prog ' + __version__)
    oParser.add_option('-o', '--output', type=str, default='', help='Output to file')
    oParser.add_option('-s', '--separator', default=';', help='Separator character (default ;)')
    (options, args) = oParser.parse_args()

    if len(args) == 0:
        oParser.print_help()
    else:
        NmapXmlParser(ExpandFilenameArguments(args), options)


if __name__ == '__main__':
    Main()
