import streamlit as st
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from difflib import Differ
import re
from typing import Union, List, Dict, Any, Tuple
from copy import deepcopy


def detect_file_type(content: str) -> str:
    """Detect if content is JSON or XML"""
    content = content.strip()
    if content.startswith("{") or content.startswith("["):
        try:
            json.loads(content)
            return "json"
        except json.JSONDecodeError:
            pass

    if content.startswith("<?xml") or content.startswith("<"):
        try:
            ET.fromstring(content)
            return "xml"
        except ET.ParseError:
            pass

    raise ValueError("Unsupported file format. Please upload a valid JSON or XML file.")


def load_file(uploaded_file) -> Tuple[Any, str]:
    """Load and parse file, detecting type automatically"""
    if uploaded_file is not None:
        content = uploaded_file.read().decode("utf-8")
        file_type = detect_file_type(content)

        if file_type == "json":
            return json.loads(content), file_type
        elif file_type == "xml":
            return ET.fromstring(content), file_type
    return None, None


def modify_json(json_data: Union[List, Dict]) -> Union[List, Dict]:
    """Modify JSON data"""
    if json_data is None:
        return None

    modified_data = json.loads(json.dumps(json_data))

    if isinstance(modified_data, list):
        for item in modified_data:
            if isinstance(item, dict):
                item["user_query"] = (
                    "Display Hunter Dickinson's jump shots under guard from the second half of the last game, last season, and previous season"
                )
                item["new"] = "Something"
                if "parameters" in item and "offensive_player" in item["parameters"]:
                    del item["parameters"]["offensive_player"]
    elif isinstance(modified_data, dict):
        modified_data["new_field"] = "This is a new value"
        if "to_delete" in modified_data:
            del modified_data["to_delete"]

    return modified_data


def modify_xml(xml_root: ET.Element) -> ET.Element:
    """Modify XML data"""
    # Create a deep copy of the XML tree
    modified_root = deepcopy(xml_root)

    # 1. Delete team_name field
    for params in modified_root.findall(".//parameters"):
        for team_name in params.findall("team_name"):
            params.remove(team_name)

    # 2. Add new parameter 'something' with value 2
    for params in modified_root.findall(".//parameters"):
        new_elem = ET.SubElement(params, "something")
        new_elem.text = "2"

    # 3. Update shot_type to 'points'
    for shot_type in modified_root.findall(".//shot_type"):
        shot_type.text = "points"

    return modified_root


def prettify_xml(elem: ET.Element) -> str:
    """Return a pretty-printed XML string"""
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")


def generate_diff(original: Any, modified: Any, file_type: str) -> List[str]:
    """Generate a diff between two objects based on file type"""
    if not original or not modified:
        return []

    if file_type == "json":
        original_str = json.dumps(original, indent=2).split("\n")
        modified_str = json.dumps(modified, indent=2).split("\n")
    else:  # xml
        original_str = prettify_xml(original).split("\n")
        modified_str = prettify_xml(modified).split("\n")

    differ = Differ()
    return list(differ.compare(original_str, modified_str))


def format_diff_html(diff_lines: List[str]) -> str:
    """Convert diff lines to HTML with color formatting"""
    html_lines = []
    for line in diff_lines:
        if line.startswith("+"):
            formatted_line = f'<div style="background-color: #a8ffa8">{line}</div>'
        elif line.startswith("-"):
            formatted_line = f'<div style="background-color: #ffb3b3">{line}</div>'
        elif line.startswith("?"):
            continue
        else:
            formatted_line = f"<div>{line}</div>"
        html_lines.append(formatted_line)

    return "".join(html_lines)


def get_file_download_info(data: Any, file_type: str) -> tuple:
    """Get file download info based on file type"""
    if file_type == "json":
        content = json.dumps(data, indent=2)
        mime = "application/json"
        extension = "json"
    else:  # xml
        content = prettify_xml(data)
        mime = "application/xml"
        extension = "xml"

    return content, mime, extension


def main():
    st.title("File Diff Viewer")

    # File upload - now accepts both JSON and XML
    uploaded_file = st.file_uploader("Upload JSON or XML file", type=["json", "xml"])

    if uploaded_file:
        try:
            # Load original file and detect type
            original_data, file_type = load_file(uploaded_file)

            if original_data is not None:
                # Show detected file type
                st.info(f"Detected file type: {file_type.upper()}")

                # Modify data based on detected type
                if file_type == "json":
                    modified_data = modify_json(original_data)
                else:  # xml
                    modified_data = modify_xml(original_data)

                # Generate and display diff
                st.subheader("Differences (Git-style)")
                diff_lines = generate_diff(original_data, modified_data, file_type)
                diff_html = format_diff_html(diff_lines)
                st.markdown(diff_html, unsafe_allow_html=True)

                # Add download button for modified file
                content, mime, extension = get_file_download_info(
                    modified_data, file_type
                )
                st.download_button(
                    label=f"Download modified {file_type.upper()}",
                    data=content,
                    file_name=f"modified.{extension}",
                    mime=mime,
                )
        except ValueError as e:
            st.error(str(e))


if __name__ == "__main__":
    main()
