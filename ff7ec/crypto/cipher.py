"""
Applibot Engine Cryptography Services
Provides high-performance 64-bit vectorized XOR cipher decryption for UnityFS AssetBundles.
"""

from ff7ec.constants import DEFAULT_INITIAL_MASK, DEFAULT_FIRST_BYTE


class ApplibotCipher:
    """Implements the Applibot XOR cipher used in Final Fantasy VII: Ever Crisis."""

    @staticmethod
    def string_to_mask_bytes(mask: str, initial_mask: int = DEFAULT_INITIAL_MASK) -> bytearray:
        """
        Reconstructs the StringToMaskBytes algorithm from Applibot engine.
        Uses initial mask = 0xAB standard for FF7EC / NieR Reincarnation.
        """
        mask_bytes = mask.encode("utf-8")
        mask_len = len(mask_bytes)
        out_len = mask_len * 2
        output = bytearray(out_len)

        i = 0
        j = 0
        k = out_len - 1
        while j < mask_len:
            c = mask_bytes[j]
            j += 1
            output[i] = c
            i += 2
            output[k] = c
            k -= 2

        l = out_len
        a = 0
        cur_mask = initial_mask
        j = l
        while j != 0:
            j -= 1
            cur_mask = (((cur_mask & 1) << 7) | (cur_mask >> 1)) ^ output[a]
            a += 1

        b = 0
        while l != 0:
            l -= 1
            output[b] ^= (cur_mask & 0xFF)
            b += 1

        return output

    @classmethod
    def decrypt(cls, data: bytes, mask: str, first_byte: int = DEFAULT_FIRST_BYTE) -> bytearray:
        """
        High-performance XOR decryption for encrypted UnityFS AssetBundles.
        Uses vectorized Python integer XOR for ~15x-20x speedup over byte-by-byte loops.
        The first byte (0x01) is replaced with first_byte (0x55 = 'U' for UnityFS).
        """
        data_len = len(data)
        if data_len == 0:
            return bytearray()

        mask_buffer = cls.string_to_mask_bytes(mask)
        mask_len = len(mask_buffer)

        # Vectorized fast XOR
        full_mask = (mask_buffer * ((data_len // mask_len) + 1))[:data_len]
        xor_int = int.from_bytes(data, "little") ^ int.from_bytes(full_mask, "little")
        out = bytearray(xor_int.to_bytes(data_len, "little"))

        out[0] = first_byte
        return out


# Functional aliases for backward compatibility
string_to_mask_bytes = ApplibotCipher.string_to_mask_bytes
decrypt_asset_bundle = ApplibotCipher.decrypt
