from transformers import HfArgumentParser

from ltx_video.inference import InferenceConfig, infer


def main() -> None:
    parser = HfArgumentParser(InferenceConfig)
    config = parser.parse_args_into_dataclasses()[0]
    infer(config=config)


if __name__ == "__main__":
    main()
