from zone import Zone, ZoneType
from connection import Connection
import sys

class Parser:
    """
    Responsible for reading and validating a map file and converting it
    into structured simulation objects.

    The parser builds the full graph definition, including:
    - zones (start, end, and hubs)
    - connections between zones
    - simulation metadata (ex number of drones)

    It performs strict validation to ensure the map file is well-formed,
    rejecting invalid configurations early.
    """

    def __init__(self, map_file: str) -> None:
        """
        Initializes the parser with the path to a map file.

        Args:
            map_file: Path to the input map definition file.
        """
        self.map_file = map_file

    def parse_metadata(self, metadata: str) -> dict[str, str]:
        """
        Extracts key-value metadata pairs from a bracketed string.

        Example:
            "[zone=restricted color=red]" → {"zone": "restricted", "color": "red"}

        Args:
            metadata: Raw metadata string including brackets.

        Returns:
            Dictionary containing parsed key-value pairs.
        """
        # Remove the surrounding brackets [ ] and whitespace
        metadata = metadata.strip().strip("[]")

        result: dict[str, str] = {}

        # Each item is separated by a space, ex 'zone=restricted color=red'
        for item in metadata.split():
            if "=" in item:
                key, value = item.split("=", 1)  # split on first '=' only
                result[key] = value

        return result

    def parse_zone_type(self, zone_str: str, line_num: int) -> ZoneType:
        """Convert a zone type string to a ZoneType enum value.

        Args:
            zone_str: The zone type string, ex 'restricted'
            line_num: The line number in the file (used in error messages)

        Returns:
            The matching ZoneType enum value

        """
        # Map each valid string to its ZoneType enum value
        valid_types: dict[str, ZoneType] = {
            "normal": ZoneType.NORMAL,
            "blocked": ZoneType.BLOCKED,
            "restricted": ZoneType.RESTRICTED,
            "priority": ZoneType.PRIORITY,
        }
        if zone_str not in valid_types:
            print("\033[31m" + 
                f"Line {line_num}: invalid zone type '{zone_str}'. "
                f"Must be one of: {list(valid_types.keys())}" + "\033[0m"
            )
            sys.exit(1)

        return valid_types[zone_str]

    def parse_hub_line(self, value: str, line_num: int) -> tuple[str, int, int, dict[str, str]]:
        """Parse the content of a hub line after the prefix.

        Example input: 'roof1 3 4 [zone=restricted color=red]'

        Args:
            value: The part of the line after 'hub: '
            line_num: The line number (used in error messages)

        Returns:
            A tuple of (name, x, y, metadata_dict)
        """
        # Separate the metadata block [...] from the rest if it exists
        if "[" in value:
            # Split at the first '[' to get the main part and the metadata
            main_part, meta_part = value.split("[", 1)
            meta_part = "[" + meta_part  # restore the bracket for parse_metadata
        else:
            main_part = value
            meta_part = ""

        # The main part has: name x y
        parts = main_part.strip().split()
        if len(parts) != 3:
            print("\033[31m" +
                f"Line {line_num}: expected 'name x y' but got '{main_part.strip()}'" + "\033[0m"
            )
            sys.exit(1)

        name = parts[0]
        # Zone names cannot contain dashes (connection syntax uses dashes as separator)
        if "-" in name:
            print("\033[31m" + f"Line {line_num}: zone name '{name}' cannot contain dashes" + "\033[0m")
            sys.exit(1)

        # Parse x and y as integers
        try:
            x = int(parts[1])
            y = int(parts[2])
        except ValueError:
            print("\033[31m" +
                f"Line {line_num}: coordinates must be integers, got '{parts[1]}' and '{parts[2]}'" + "\033[0m"
            )

        metadata = self.parse_metadata(meta_part) if meta_part else {}
        return name, x, y, metadata

    def get_map_data(self) -> tuple[int, Zone, Zone, list[Zone], list[Connection]]:
        """Parse the map file and return all map data as typed objects.

        Returns:
            A tuple of (nb_drones, start_zone, end_zone, hubs, connections)

        """
        nb_drones: int = 0
        start_zone: Zone | None = None
        end_zone: Zone | None = None
        hubs: list[Zone] = []
        connections: list[Connection] = []

        # Keep a dict of all zones by name so connections can look them up
        all_zones: dict[str, Zone] = {}

        # Track seen connections to detect duplicates (ex a-b and b-a)
        seen_connections: set[frozenset[str]] = set()

        with open(self.map_file, "r") as file:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # The first non-comment line must define nb_drones
                if nb_drones == 0:
                    if not line.startswith("nb_drones:"):
                        print("\033[31m" +
                            f"Line {line_num}: first line must be 'nb_drones: <number>'" + "\033[0m"
                        )
                        sys.exit(1)
                    try:
                        nb_drones = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        print("\033[31m" +
                            f"ERROR: Line {line_num}: nb_drones must be a positive integer" + "\033[0m"
                        )
                        sys.exit(1)
                    continue

                # Split into prefix and value at the first ': '
                if ": " not in line:
                    print("\033[31m" + f"ERROR: Line {line_num}: unrecognized line format: '{line}'" + "\033[0m")
                    sys.exit(1)

                prefix, value = line.split(": ", 1)
                prefix = prefix.strip()
                value = value.strip()

                # Handle hub types
                if prefix in ("hub", "start_hub", "end_hub"):
                    name, x, y, meta = self.parse_hub_line(value, line_num)

                    # Check for duplicate zone names
                    if name in all_zones:
                        print("\033[31m" + f"ERROR: Line {line_num}: duplicate zone name '{name}'" + "\033[0m")
                        sys.exit(1)

                    # Get zone type from metadata, defaulting to NORMAL
                    zone_type_str = meta.get("zone", "normal")
                    zone_type = self.parse_zone_type(zone_type_str, line_num)

                    # Get max_drones from metadata, defaulting to 1
                    max_drones = 1
                    if "max_drones" in meta:
                        try:
                            max_drones = int(meta["max_drones"])
                        except ValueError:
                            print("\033[31m" +
                                f"ERROR: Line {line_num}: max_drones must be a positive integer" + "\033[0m"
                            )
                            sys.exit(1)

                    color = meta.get("color", None)

                    zone = Zone(
                        name=name,
                        x=x,
                        y=y,
                        zone_type=zone_type,
                        max_drones=max_drones,
                        color=color,
                    )

                    # Register the zone by its role
                    if prefix == "start_hub":
                        if start_zone is not None:
                            print("\033[31m" + f"ERROR: Line {line_num}: duplicate start_hub" + "\033[0m")
                            sys.exit(1)
                        start_zone = zone
                    elif prefix == "end_hub":
                        if end_zone is not None:
                            print("\033[31m" + f"ERROR: Line {line_num}: duplicate end_hub" + "\033[31m")
                            sys.exit(1)
                        end_zone = zone
                    else:
                        hubs.append(zone)

                    all_zones[name] = zone

                # Handle connections
                elif prefix == "connection":
                    # Separate zone names from optional metadata
                    if "[" in value:
                        conn_part, meta_part = value.split("[", 1)
                        meta_part = "[" + meta_part
                    else:
                        conn_part = value
                        meta_part = ""

                    conn_part = conn_part.strip()

                    # Connection format: zone1-zone2
                    if "-" not in conn_part:
                        print("\033[31m" +
                            f"ERROR: Line {line_num}: connection must be 'zone1-zone2', got '{conn_part}'" + "\033[0m"
                        )
                        sys.exit(1)

                    zone1_name, zone2_name = conn_part.split("-", 1)

                    # Both zones must have been defined before the connection
                    if zone1_name not in all_zones:
                        print("\033[31m" +
                            f"ERROR: Line {line_num}: unknown zone '{zone1_name}'" + "\033[0m"
                        )
                        sys.exit(1)
                    if zone2_name not in all_zones:
                        print("\033[31m" +
                            f"ERROR: Line {line_num}: unknown zone '{zone2_name}'" + "\033[0m"
                        )
                        sys.exit(1)

                    # Detect duplicate connections (a-b and b-a are the same)
                    conn_key = frozenset([zone1_name, zone2_name])
                    if conn_key in seen_connections:
                        print("\033[31m" +
                            f"ERROR: Line {line_num}: duplicate connection '{conn_part}'" + "\033[0m"
                        )
                        sys.exit(1)
                    seen_connections.add(conn_key)

                    # Parse max_link_capacity from metadata
                    meta = self.parse_metadata(meta_part) if meta_part else {}
                    max_link_capacity = 1
                    if "max_link_capacity" in meta:
                        try:
                            max_link_capacity = int(meta["max_link_capacity"])
                        except ValueError:
                            print("\033[31m" +
                                f"ERROR: Line {line_num}: max_link_capacity must be a positive integer" + "\033[0m"
                            )
                            sys.exit(1)

                    connection = Connection(
                        zone1=all_zones[zone1_name],
                        zone2=all_zones[zone2_name],
                        max_link_capacity=max_link_capacity,
                    )
                    connections.append(connection)

                else:
                    print("\033[31m" + f"ERROR: Line {line_num}: unknown prefix '{prefix}'" + "\033[0m")
                    sys.exit(1)

        # Final validations
        if start_zone is None:
            print("\033[31m" + "ERROR: Map has no start_hub defined" + "\033[0m")
            sys.exit(1)
        if end_zone is None:
            print("\033[31m" + "ERROR: Map has no end_hub defined" + "\033[0m")
            sys.exit(1)

        return nb_drones, start_zone, end_zone, hubs, connections