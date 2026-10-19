import argparse
import json
import sys

from .pipeline import extract_orders


def main() -> int:
    arg_parser = argparse.ArgumentParser(description="Odczyt pozycji ze zdjęcia notatki")
    arg_parser.add_argument("image", help="ścieżka do zdjęcia")
    arg_parser.add_argument("--json", action="store_true", help="wynik jako JSON")
    arg_parser.add_argument("--debug", action="store_true", help="pokaż surowy tekst z OCR")
    arg_parser.add_argument("--no-enhance", action="store_true", help="wyłącz poprawę kontrastu")
    args = arg_parser.parse_args()

    result = extract_orders(args.image, enhance_contrast=not args.no_enhance)
    groups = result.groups()

    if args.json:
        print(json.dumps(groups, ensure_ascii=False, indent=2))
        return 0

    if args.debug:
        print("=== SUROWY TEKST Z OCR ===")
        for line in result.ocr_lines:
            print(f"  [{line.confidence:.2f}] {line.text}")
        print()

    if not groups:
        print("(nic nie rozpoznano -- spróbuj --debug, żeby zobaczyć co odczytał OCR)")

    for number, group in enumerate(groups, start=1):
        hint = f"  (tekst z notatki: {group['marker_text']})" if group["marker_text"] else ""
        print(f"=== GRUPA {number}{hint} ===")
        for order in group["orders"]:
            flag = "SPRAWDŹ" if order["needs_review"] else "ok     "
            print(
                f"  [{flag}] {order['name']:>6} | {order['length_mm']:g} x "
                f"{order['height_mm']:g} | {order['quantity']} szt"
            )
            for warning in order["warnings"]:
                print(f"             ! {warning}")

    if result.unparsed_lines:
        print("=== DO RĘCZNEGO PRZEPISANIA ===")
        for line in result.unparsed_lines:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())