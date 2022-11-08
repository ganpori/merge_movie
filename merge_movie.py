import datetime
from pathlib import Path

from moviepy import editor


def main():
    path_data_dir = Path("G:/DCIM/100GOPRO")
    list_path_mp4 = [path for path in path_data_dir.glob("*.mp4")]
    list_path_mp4.sort()

    latest_file_stat = list_path_mp4[0].stat()
    datetime_latest_file_mtime = datetime.datetime.fromtimestamp(
        latest_file_stat.st_mtime
    )  # mtimeはファイルの最終更新日時.JSTかUTC化に注意。windowsでやった時はなぜかJSTになってた

    path_output_mp4 = Path(f"{datetime_latest_file_mtime.strftime('%Y%m%d')}.mp4")

    # 動画情報の取得
    list_clip = [editor.VideoFileClip(str(path_mp4)) for path_mp4 in list_path_mp4]

    clip_merged = editor.concatenate_videoclips(list_clip)

    clip_merged.write_videofile(str(path_output_mp4))
    return


if __name__ == "__main__":
    main()
