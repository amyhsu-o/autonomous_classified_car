## 環境安裝

-   使用 `pip` 安裝

    ```bash
    $ pip install -r requirements.txt
    ```

-   使用 `poetry` 安裝

    ```bash
    $ poetry install --no-root
    ```

## 環境設定

依照 `.env.example` 建立 `.env`

-   base case 寫法：

    1. 第一次執行先隨意填寫
    2. 第一次執行時，先以一顆小球正對著相機量測球和相機的距離，紀錄於 `BASE_DISANCE`
    3. 與 2. 同時看 console 輸出結果中的 radius 欄位，紀錄於 `BASE_RADIUS`

-   註：相機目前設定為編號 0 號相機

## 執行

```bash
$ python main.py
```

## Serial 傳輸形式

```json
{
    "data": {
        "angle": ...,
        "dist": ...,
        "color": ...
    }
}
```

當有偵測到球的時候才會傳，如果持續偵測到球，過程中每 5 秒會更新當下狀況再傳一次。

-   angle — 以正前方為 0 度，順時針為正、逆時針為負；單位為：度 °
-   color — 會傳數字，對應關係如下

    ```py
    COLOR = {
        0: "Red",
        1: "Yellow",
        2: "Blue"
    }
    ```
