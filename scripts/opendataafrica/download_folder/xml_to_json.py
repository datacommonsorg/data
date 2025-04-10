"""Converts an xml file to json file."""
import json
from absl import app
from absl import flags
import xmltodict

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'input_xml', None, 'Input xml file to convert to json.', required=True
)
flags.DEFINE_string('output_json', None, 'Output json file.', required=True)

def convert_xml_to_json(input_xml_path: str, output_json_path: str) -> None:
    """Converts an XML file to a JSON file.

    Args:
        input_xml_path: The path to the input XML file.
        output_json_path: The path to the output JSON file.
    """
    try:
        with open(input_xml_path, 'r') as xml_file:
            xml_data = xml_file.read()

        if xml_data:
            data_dict = xmltodict.parse(xml_data)
            json_data = json.dumps(data_dict, indent=4)
            with open(output_json_path, 'w') as json_file:
                json_file.write(json_data)
        else:
            with open(output_json_path, 'w') as json_file:
                json_file.write('{}')
    except FileNotFoundError:
        print(f"Error: Input XML file not found at '{input_xml_path}'")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")

def main(argv):
    if len(argv) > 1:
        raise app.UsageError('Too many command-line arguments.')
    convert_xml_to_json(_FLAGS.input_xml, _FLAGS.output_json)

if __name__ == '__main__':
    app.run(main)