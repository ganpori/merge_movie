from pathlib import Path

from moviepy import editor


def main():
    list_path_mp4 = [path for path in Path("data").glob("*.mp4")]
    list_path_mp4.sort()

    path_output_mp4 = Path("hoge.mp4")

    # 動画情報の取得
    list_clip = [editor.VideoFileClip(str(path_mp4)) for path_mp4 in list_path_mp4]

    clip_merged = editor.concatenate_videoclips(list_clip)

    clip_merged.write_videofile(str(path_output_mp4))
    return


if __name__ == "__main__":
    main()
