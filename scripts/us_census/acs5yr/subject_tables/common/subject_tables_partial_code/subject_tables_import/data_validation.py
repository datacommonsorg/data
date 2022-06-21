import csv 
import os
import re
from absl import flags, app

FLAGS = flags.FLAGS
flags.DEFINE_string('csv_path', '~/Documents/acs_tables/S0701/run2/S0701_cleaned.csv', 'Path to the input csv')
flags.DEFINE_string('out_csv_path', '~/Documents/acs_tables/S0701/run2/S0701_cleaned_fixed.csv','Path to the fixed, clean csv')
flags.DEFINE_string('log_csv_path', '~/Documents/acs_tables/S0701/run2/S0701_fix_required.csv','Path to the csv log')

# csv_path = os.path.expanduser('~/Documents/acs_tables/S0701/run2/S0701_cleaned.csv')
# out_csv_path = os.path.expanduser('~/Documents/acs_tables/S0701/run2/S0701_cleaned_fixed.csv')
# log_csv_path = os.path.expanduser('~/Documents/acs_tables/S0701/run2/S0701_fix_required.csv')

def fix_open_distributions_in_observation_csv(argv):
    """
    Function to fix the open distributions in the StatVarObservation values
    """

    csv_path = os.path.expanduser(FLAGS.csv_path)
    out_csv_path = os.path.expanduser(FLAGS.out_csv_path)
    log_csv_path = os.path.expanduser(FLAGS.log_csv_path)
    
    csv_reader = csv.reader(open(csv_path, 'r'))
    csv_writer = csv.writer(open(out_csv_path, 'w'))
    log_csv_writer = csv.writer(open(log_csv_path, 'w'))
    
    for row in csv_reader:
        if csv_reader.line_num == 1:
            csv_writer.writerow(row)
            log_csv_writer.writerow(row)
        else:
            try:
                float(row[3])
                csv_writer.writerow(row)
            except ValueError:
                print(','.join(row))
                log_csv_writer.writerow(row)
                row[3] = re.sub("\W", "", row[3])
                csv_writer.writerow(row)

if __name__ == '__main__':
    app.run(fix_open_distributions_in_observation_csv)

