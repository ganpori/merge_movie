from pathlib import Path

import cv2


def combine_movie(list_path_mp4, path_output_mp4, fps, width, height):
    fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")

    out = cv2.VideoWriter(
        path_output_mp4.as_posix(), int(fourcc), fps, (int(width), int(height))
    )

    for path_mp4 in list_path_mp4:
        movie = cv2.VideoCapture(str(path_mp4))

        # 正常に動画ファイルを読み込めたか確認
        if movie.isOpened() == True:
            # read():1コマ分のキャプチャ画像データを読み込む
            ret, frame = movie.read()
        else:
            ret = False

        while ret:
            # 読み込んだフレームを書き込み
            out.write(frame)
            # 次のフレーム読み込み
            ret, frame = movie.read()

    return


def main():
    list_path_mp4 = [path for path in Path("data").glob("*.mp4")]
    list_path_mp4.sort()

    path_output_mp4 = Path("hoge.mp4")

    # 動画情報の取得
    movie = cv2.VideoCapture(list_path_mp4[0].as_posix())
    fps = movie.get(cv2.CAP_PROP_FPS)
    height = movie.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = movie.get(cv2.CAP_PROP_FRAME_WIDTH)

    combine_movie(list_path_mp4, path_output_mp4, fps, width, height)
    return


if __name__ == "__main__":
    main()
