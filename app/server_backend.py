from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=3000, type=int)
    args = parser.parse_args()
    uvicorn.run("facedeploy_core.api:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    main()
