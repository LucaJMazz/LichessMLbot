import zstandard as zstd
import json
import ast
import sys
from pathlib import Path

def parse_line(raw_line: bytes):
    """
    Try strict JSON first. If that fails (e.g. single-quoted Python-dict-style
    lines like your sample), fall back to literal_eval, then re-serialize as
    proper JSON.
    """
    text = raw_line.decode('utf-8', errors='replace').strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            obj = ast.literal_eval(text)
            return obj
        except (ValueError, SyntaxError):
            return None


def extract_n_bytes(input_path: str, output_path: str,
                     target_bytes: int = 20 * 1024**3,
                     chunk_size: int = 1024 * 1024 * 16):
    input_path = Path(input_path)
    output_path = Path(output_path)
    dctx = zstd.ZstdDecompressor()

    total_lines = 0
    kept_lines = 0
    malformed = 0
    bytes_written = 0

    with open(input_path, 'rb') as ifh, open(output_path, 'w', encoding='utf-8') as ofh:
        with dctx.stream_reader(ifh, read_size=chunk_size) as reader:
            buffer = b""
            while bytes_written < target_bytes:
                chunk = reader.read(chunk_size)
                if not chunk:
                    break
                buffer += chunk
                *lines, buffer = buffer.split(b"\n")

                for raw_line in lines:
                    if not raw_line.strip():
                        continue
                    total_lines += 1

                    obj = parse_line(raw_line)
                    if obj is None:
                        malformed += 1
                        continue

                    out_line = json.dumps(obj) + "\n"
                    out_bytes = out_line.encode('utf-8')

                    ofh.write(out_line)
                    bytes_written += len(out_bytes)
                    kept_lines += 1

                    if total_lines % 50_000 == 0:
                        gb_written = bytes_written / (1024**3)
                        sys.stdout.write(
                            f"\rLines read: {total_lines:,} | kept: {kept_lines:,} | "
                            f"malformed: {malformed:,} | written: {gb_written:.2f} GB"
                        )
                        sys.stdout.flush()

                    if bytes_written >= target_bytes:
                        break

    gb_written = bytes_written / (1024**3)
    print(f"\nDone.")
    print(f"  Total lines read:   {total_lines:,}")
    print(f"  Malformed skipped:  {malformed:,}")
    print(f"  Lines written:      {kept_lines:,}")
    print(f"  Output size:        {gb_written:.2f} GB")
    print(f"  Output file:        {output_path}")


if __name__ == "__main__":
    input_file = "/Users/Luca/Downloads/lichess_db_eval.jsonl.zst"       # your compressed source file
    output_file = "/Users/Luca/Downloads/output.jsonl" # output for the ML pipeline
    target_gb = 20

    extract_n_bytes(
        input_file,
        output_file,
        target_bytes=target_gb * 1024**3
    )