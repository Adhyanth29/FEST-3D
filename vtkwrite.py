import sys
import os
import getopt
import numpy as np

def parse_grid(filename):
    f = open(filename)
    d = f.read()
    f.close()
    d = d.splitlines()

    x = []
    y = []

    gridsize = d.pop(0)  # The first line of the file should contain imx, jmx
    gridsize = gridsize.strip()
    gridsize = gridsize.split(' ')
    gridsize = [int(gridsize[0]), int(gridsize[-1])]

    for point in d:
        p = point
        p = p.strip()
        t = p.split(' ')
        x.append(float(t[0]))
        y.append(float(t[-1]))

    x = np.array(x)
    y = np.array(y)
    grid = {
        'x': x,
        'y': y,
    }
    return (grid, gridsize)

def read_data(filename, gridsize):
    '''Reads data in from a file generated by fortran (has a specific structure)

    filename --> Name of the file
    gridsize --> Grid size (imx, jmx)
    '''

    f = open(filename)
    raw = f.read()
    f.close()
    raw = raw.splitlines()

    d = {}

    imx, jmx = gridsize

    label = None
    curr_data_type = ''
    curr_dim = 0

    # The first line is a comment
    d['Comment'] = raw.pop(0).strip()
    d['CELL_DATA'] = {}
    d['POINT_DATA'] = {}

    for l in raw:
        l = l.strip()
        # Use the label to create a new dataset in the appropriate dictionary
        if l.upper() == 'CELLDATA':
            # A new CELLDATA dataset was found
            curr_data_type = 'CELL_DATA'
            # The previous data set has ended
            # Convert it to a numpy array and reset label
            if label is not None:
                d[curr_data_type][label] = np.array(d[curr_data_type][label])
            label = ''
            continue
        elif l.upper() == 'POINTDATA':
            # A new POINTDATA dataset was found
            curr_data_type = 'POINT_DATA'
            # The previous data set has ended
            # Convert it to a numpy array and reset label
            if label is not None:
                d[curr_data_type][label] = np.array(d[curr_data_type][label])
            label = ''
            continue
        if not label:
            # No label is currently set
            # Also, the current line does not indicate the start of a new 
            # dataset. So this must be a new label.
            label = l
            d[curr_data_type][label] = []
            continue
        # Read in the data
        p = l
        # Remove blanks
        p = p.split(' ')
        while 1:
            try:
                p.remove('')
            except ValueError:
                break
        curr_dim = len(p)
        for k in range(curr_dim):
            p[k] = float(p[k])
        if curr_dim == 1:
            p = p[0]
        d[curr_data_type][label].append(p)
    d[curr_data_type][label] = np.array(d[curr_data_type][label])
    return d

def writevtk(grid, gridsize, data, filename, comment=None):
    '''Writes the grid and data in vtk format'''

    f = open(filename + '.part', 'w')

    imx, jmx = gridsize
    num_points = imx * jmx
    num_cells = (imx - 1) * (jmx - 1)

    # Write Header
    f.write('# vtk DataFile Version 3.1\n')
    comment = data.get('Comment', comment)
    if comment:
        f.write(comment)
    else:
        f.write('Glomar response.')
    f.write('\n')
    f.write('ASCII\n')
    f.write('DATASET UNSTRUCTURED_GRID\n')
    f.write('\n')

    # Write Pointdata
    f.write('POINTS ')
    f.write(str(num_points))
    f.write(' FLOAT\n')
    for i in range(num_points):
        f.write(str(grid['x'][i]))
        f.write(' ')
        f.write(str(grid['y'][i]))
        f.write(' ')
        f.write('0')  # z coordinate
        f.write('\n')
    f.write('\n')

    # Write Celldata
    f.write('CELLS ')
    f.write(str(num_cells))
    f.write(' ')
    f.write(str(num_cells * 5))
    f.write('\n')
    for j in range(jmx - 1):
        for i in range(imx - 1):
            f.write('4 ')
            f.write(str(j*imx + i))  # Point i, j
            f.write(' ')
            f.write(str(j*imx + (i+1)))  # Point i+1, j
            f.write(' ')
            f.write(str((j+1)*imx + (i+1)))  # Point i+1, j+1
            f.write(' ')
            f.write(str((j+1)*imx + i))  # Point i, j+1
            f.write('\n')
    f.write('\n')
    f.write('CELL_TYPES ')
    f.write(str(num_cells))
    f.write('\n')
    f.write(('9 ' * num_cells).strip())
    f.write('\n')

    # Write Celldatasets
    for key in data['CELL_DATA']:
        f.write('CELL_DATA ')
        f.write(str(num_cells))
        f.write('\n')
        if isinstance(data['CELL_DATA'][key][0], np.ndarray):
            f.write('VECTORS ')
            f.write(key)
            f.write(' FLOAT\n')
        else:
            f.write('SCALARS ')
            f.write(key)
            f.write(' FLOAT\n')
            f.write('LOOKUP_TABLE default\n')
        for elem in data['CELL_DATA'][key]:
            if not isinstance(elem, np.ndarray):
                # It is scalar data
                f.write(str(elem))
                f.write('\n')
            else:
                buf = ''
                for j in elem:
                    buf += str(j) + ' '
                if len(elem) == 2:
                    buf += '0.0'
                buf.strip()
                f.write(buf)
                f.write('\n')
        f.write('\n')

    f.close()

    # Rename the file: remove the .part from the end.
    os.rename(filename + '.part', filename)

def translate_fortran_to_vtk(gridfile, datafile, opfilename, filecomment):
    (grid, gridsize) = parse_grid(gridfile)
    data = read_data(datafile, gridsize)
    writevtk(grid, gridsize, data, opfilename, filecomment)

def commandline_option_interface(argv):
    gridfile = 'grid.txt'
    datafile = 'data.txt'
    outputfile = 'output.vtk'
    outputdesc = 'Output of vtkwrite'
    try:
        opts, args = getopt.getopt(argv, 'hg:d:o:c:', ['help', 'gridfile=', 'datafile=', 'outputfile=', 'outputdesc='])
    except getopt.GetoptError:
        print 'Usage: python vtkwrite.py -g <gridfile> -d <datafile> -o <outputfile> -c <output file comment>'
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print 'Usage:'
            print 'python vtkwrite.py -g <gridfile> -d <datafile> -o <outputfile> -c <output file comment>'
            print 'The following verbose options can also be used:'
            print '  --help                                           (synonymous with -h)'
            print '  --gridfile=<gridfile>                            (synonymous with -g)'
            print '  --datafile=<datafile>                            (synonymous with -d)'
            print '  --outputfile=<outputfile>                        (synonymous with -o)'
            print '  --outputdesc=<output file comment / description> (synonymous with -c)'
            sys.exit()
        elif opt in ('-g', '--gridfile'):
            gridfile = arg
        elif opt in ('-d', '--datafile'):
            datafile = arg
            if outputfile == 'output.vtk':
                outputfile = datafile.split('.')[0] + '.vtk'
        elif opt in ('-o', '--outputfile'):
            outputfile = arg
        elif opt in ('-c', '--outputdesc'):
            outputdesc = arg

    print 'Translating file ', datafile

    translate_fortran_to_vtk(gridfile, datafile, outputfile, outputdesc)

def iesolve_output_converter():
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    files = [f for f in files if f[:6] == 'output' and f[-5:] == '.fvtk']
    files.sort()
    for f in files:
        print 'Translating file ' + f
        translate_fortran_to_vtk('bumpgrid.txt', f, f.split('.')[0] + '.vtk', 'IESolver Output')
    print 'It is done!'

def iesolve_output_converter2():
    for f in range(1, 50):
        filename = '%s%05d%s' % ('output', f, '.fvtk')
        print 'Translating file ', filename
        translate_fortran_to_vtk('bumpgrid.txt', filename, filename.split('.')[0] + '.vtk', 'IESolver Output')
    print 'It is done!'

if __name__ == '__main__':
   #commandline_option_interface(sys.argv[1:])
   iesolve_output_converter()
