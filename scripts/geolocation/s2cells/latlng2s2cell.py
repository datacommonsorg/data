import s2sphere
from absl import app
from absl import flags

FLAGS = flags.FLAGS

flags.DEFINE_float('lat', 0, 'Latitude')
flags.DEFINE_float('lng', 0, 'Longitude')
flags.DEFINE_integer('level', 10, 'S2 Cell level')


def latlng2s2cell(level, lat, lng):
    assert level >= 0 and level <= 30
    ll = s2sphere.LatLng.from_degrees(lat, lng)
    cell = s2sphere.CellId.from_lat_lng(ll)
    if level < 30:
        cell = cell.parent(level)
    cid = '{0:#0{1}x}'.format(cell.id(), 18)
    print(cid)


def main(_):
    latlng2s2cell(FLAGS.level, FLAGS.lat, FLAGS.lng)


if __name__ == "__main__":
    app.run(main)

