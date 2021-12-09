import os
import s2sphere
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_integer('s2cell_level', 10, 'S2 Cell level to generate: 0 - 30')
flags.DEFINE_string('output_mcf_dir', '/tmp', 'Output directory path.')


_MCF_FORMAT = """
Node: dcid:s2Cell/{cid}
typeOf: dcs:{typeof}
name: "L{level} S2 Cell {cid}"
latitude: "{lat}"
longitude: "{lng}"
"""


def llformat(ll):
    # 4 decimal degree is 11.1m
    # (http://wiki.gis.com/wiki/index.php/Decimal_degrees)
    return str('%.4f' % ll)


def generate(level, output_dir):
    # To avoid blow-up, don't go past level 12.
    assert level >= 0 and level <= 12

    with open(os.path.join(output_dir, f"s2cell_level{level}.mcf"), 'w') as fp:
        typeof = 'S2CellLevel' + str(level)
        cell = s2sphere.CellId.begin(level)
        while cell != s2sphere.CellId.end(level):
            # Convert to hex and pad to 16 chars.
            # Format is from https://stackoverflow.com/a/12638477
            cid = '{0:#0{1}x}'.format(cell.id(), 18)
            latlng = cell.to_lat_lng()
            fp.write(_MCF_FORMAT.format(cid=cid,
                                        level=level,
                                        typeof=typeof,
                                        lat=llformat(latlng.lat().degrees),
                                        lng=llformat(latlng.lng().degrees)))
            cell = cell.next()


def main(_):
    generate(FLAGS.s2cell_level, FLAGS.output_mcf_dir)


if __name__ == "__main__":
    app.run(main)
