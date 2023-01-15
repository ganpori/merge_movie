import datetime
from pathlib import Path
import tempfile

from moviepy import editor


def sort_list_path_gopro_mp4(list_path_mp4):
    dict_path_mtime = {
        calc_file_mtime(path_mp4): path_mp4 for path_mp4 in list_path_mp4
    }
    list_mtime_sorted = sorted(dict_path_mtime.keys())
    list_path_sorted = [dict_path_mtime[mtime] for mtime in list_mtime_sorted]
    return list_path_sorted


def calc_file_mtime(path_file):
    # atime	アクセス時間	指定日数内にアクセスされたファイル
    # ctime	作成時間	指定日数内に属性変更されたファイル
    # mtime	修正時間（iノード管理）	指定日数内に修正、更新されたファイル

    latest_file_stat = path_file.stat()
    datetime_mtime = datetime.datetime.fromtimestamp(
        latest_file_stat.st_mtime
    )  # mtimeはファイルの最終更新日時.JSTかUTC化に注意。windowsでやった時はなぜかJSTになってた
    return datetime_mtime


def main():
    path_data_dir = Path("G:/DCIM/100GOPRO")
    list_path_mp4 = [path.absolute() for path in path_data_dir.glob("*.mp4")]
    list_path_mp4_sorted = sort_list_path_gopro_mp4(list_path_mp4=list_path_mp4)
    list_txt_str = [f"file {path}\n" for path in list_path_mp4_sorted]

    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", delete=False) as fp:
        str_path_file_list_txt = fp.name
        fp.writelines(list_txt_str)

    datetime_latest_file_mtime = calc_file_mtime(list_path_mp4_sorted[0])
    path_output_mp4 = Path(f"{datetime_latest_file_mtime.strftime('%Y%m%d')}.mp4")

    # 動画情報の取得
    list_clip = [
        editor.VideoFileClip(str(path_mp4)) for path_mp4 in list_path_mp4_sorted
    ]

    clip_merged = editor.concatenate_videoclips(list_clip)

    clip_merged.write_videofile(str(path_output_mp4))
    return


if __name__ == "__main__":
    main()
