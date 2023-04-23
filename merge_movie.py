import datetime
from pathlib import Path
import subprocess
import tempfile

import upload_video


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


def main(path_data_dir):
    list_path_mp4 = [path.absolute() for path in path_data_dir.glob("*.mp4")]

    # ffmpegに与えるファイル一覧txtの作成
    list_path_mp4_sorted = sort_list_path_gopro_mp4(list_path_mp4=list_path_mp4)
    list_txt_str = [
        f"file {path.as_posix()}\n" for path in list_path_mp4_sorted
    ]  # as_posixでバックスラッシュをやめないとffmpegが認識しない
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", delete=False) as fp:
        str_path_file_list_txt = fp.name
        fp.writelines(list_txt_str)

    # 出力される動画データ名の作成
    datetime_latest_file_mtime = calc_file_mtime(list_path_mp4_sorted[0])
    path_output_mp4 = Path(f"{datetime_latest_file_mtime.strftime('%Y%m%d')}.mp4")

    str_ffmpeg_command = f"ffmpeg -f concat -safe 0 -i {str_path_file_list_txt} -c copy  {path_output_mp4}"
    subprocess.run(str_ffmpeg_command)
    return


def remove_all_files_in_dir(path_data_dir):
    for path_data in path_data_dir.glob("*"):
        print(f"remove {path_data}")
        path_data.unlink()
    return


if __name__ == "__main__":
    path_data_dir = Path("G:/DCIM/DJI_001")
    upload_video.get_authenticated_service()  # 早めに一回認証しておいて勝手にアップロードされるようにしておく
    main(path_data_dir)
    upload_video.main()
    remove_all_files_in_dir(path_data_dir)
