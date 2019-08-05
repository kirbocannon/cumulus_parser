from textfsm import clitable
from exceptions import CannotParseOutputWithTextFSM


def _clitable_to_dict(cli_table):
    """Convert TextFSM cli_table object to list of dictionaries."""
    objs = []
    for row in cli_table:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[cli_table.header[index].lower()] = element
        objs.append(temp_dict)

    return objs


def parse_output(template_dir, platform=None, command=None, data=None):
    """Return the structured data based on the output from a network device."""
    cli_table = clitable.CliTable('index', template_dir)

    attrs = dict(
        Command=command,
        Platform=platform
    )
    try:
        cli_table.ParseCmd(data, attrs)
        structured_data = _clitable_to_dict(cli_table)
    except clitable.CliTableError as e:
        raise CannotParseOutputWithTextFSM

    return structured_data