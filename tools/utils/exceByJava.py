# An highlighted block
import optparse

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-f", "--file", dest="file",
                      help="write report to FILE", metavar="FILE")
    options, args = parser.parse_args()
    file = options.file
    hello_file = file + '/hello.txt'
    with open(hello_file, 'w') as file:
        file.write("yeeeeeeeeeeeeee")

