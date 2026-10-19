"""
Protobuf Decoding Engine for Octo Game Databases
Decodes raw protobuf binary payloads into python dictionary data structures without third-party libraries.
"""

from typing import Dict, Any

STATE_MAP = {0: "NONE", 1: "ADD", 2: "UPDATE", 3: "LATEST", 4: "DELETE"}


class ProtobufDecoder:
    """Decodes Google Protobuf binary messages for FF7EC asset manifests."""

    @staticmethod
    def decode_data_message(buf: memoryview, start: int, end: int) -> Dict[str, Any]:
        """Decodes an Octo DataMessage sub-block from the byte buffer."""
        pos = start
        item: Dict[str, Any] = {}
        while pos < end:
            tag = 0
            shift = 0
            while True:
                b = buf[pos]
                pos += 1
                tag |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7

            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                val = 0
                shift = 0
                while True:
                    b = buf[pos]
                    pos += 1
                    val |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                if field_num == 1:
                    item["id"] = val
                elif field_num == 4:
                    item["size"] = val
                elif field_num == 5:
                    item["crc"] = val
                elif field_num == 6:
                    item["generation"] = str(val)
                elif field_num == 7:
                    item["priority"] = val
                elif field_num == 8:
                    item.setdefault("tagid", []).append(val)
                elif field_num == 9:
                    item.setdefault("dependencies", []).append(val)
                elif field_num == 12:
                    item["state"] = STATE_MAP.get(val, str(val))
                elif field_num == 13:
                    item["uploadVersionId"] = val
            elif wire_type == 2:  # Length-delimited
                length = 0
                shift = 0
                while True:
                    b = buf[pos]
                    pos += 1
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                field_bytes = buf[pos:pos + length]
                pos += length
                if field_num == 2:
                    item["filepath"] = bytes(field_bytes).decode("utf-8", errors="replace")
                elif field_num == 3:
                    item["name"] = bytes(field_bytes).decode("utf-8", errors="replace")
                elif field_num == 10:
                    item["md5"] = bytes(field_bytes).decode("utf-8", errors="replace")
                elif field_num == 11:
                    item["objectName"] = bytes(field_bytes).decode("utf-8", errors="replace")
                elif field_num in (8, 9):
                    p_pos = 0
                    while p_pos < length:
                        p_val = 0
                        p_shift = 0
                        while True:
                            b = field_bytes[p_pos]
                            p_pos += 1
                            p_val |= (b & 0x7F) << p_shift
                            if not (b & 0x80):
                                break
                            p_shift += 7
                        key = "tagid" if field_num == 8 else "dependencies"
                        item.setdefault(key, []).append(p_val)
            elif wire_type == 1:
                pos += 8
            elif wire_type == 5:
                pos += 4
            else:
                raise ValueError(f"Unknown wire type {wire_type}")
        return item

    @classmethod
    def decode_octo_database(cls, raw_bytes: bytes) -> Dict[str, Any]:
        """Decodes the root Octo Database protobuf message containing assetBundleList & resourceList."""
        buf = memoryview(raw_bytes)
        pos = 0
        total_len = len(buf)
        database: Dict[str, Any] = {
            "revision": 0,
            "assetBundleList": [],
            "tagName": [],
            "resourceList": [],
            "urlFormat": "",
        }

        while pos < total_len:
            tag = 0
            shift = 0
            while True:
                b = buf[pos]
                pos += 1
                tag |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7

            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                val = 0
                shift = 0
                while True:
                    b = buf[pos]
                    pos += 1
                    val |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                if field_num == 1:
                    database["revision"] = val
            elif wire_type == 2:  # Length-delimited
                length = 0
                shift = 0
                while True:
                    b = buf[pos]
                    pos += 1
                    length |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                sub_start = pos
                sub_end = pos + length
                pos = sub_end

                if field_num == 2:
                    database["assetBundleList"].append(cls.decode_data_message(buf, sub_start, sub_end))
                elif field_num == 3:
                    database["tagName"].append(bytes(buf[sub_start:sub_end]).decode("utf-8", errors="replace"))
                elif field_num == 4:
                    database["resourceList"].append(cls.decode_data_message(buf, sub_start, sub_end))
                elif field_num == 5:
                    database["urlFormat"] = bytes(buf[sub_start:sub_end]).decode("utf-8", errors="replace")
            elif wire_type == 1:
                pos += 8
            elif wire_type == 5:
                pos += 4
            else:
                raise ValueError(f"Unknown wire type {wire_type}")

        return database


# Functional aliases for backward compatibility
_decode_octo_data_message = ProtobufDecoder.decode_data_message
_decode_octo_database = ProtobufDecoder.decode_octo_database
