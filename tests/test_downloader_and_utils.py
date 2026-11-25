"""Testes unitários para utils e downloader do CoffeeMediaDownloader Pro."""

from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import downloader
import utils


class TestUtils(unittest.TestCase):
    def test_is_valid_media_url(self) -> None:
        self.assertTrue(utils.is_valid_media_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
        self.assertTrue(utils.is_valid_media_url("https://youtu.be/dQw4w9WgXcQ"))
        self.assertTrue(utils.is_valid_media_url("https://vimeo.com/123456"))
        self.assertFalse(utils.is_valid_media_url("not a url"))
        self.assertFalse(utils.is_valid_media_url("https://youtube.com"))
        self.assertFalse(utils.is_valid_media_url("ftp://example.com/file.mp4"))
        self.assertFalse(utils.is_valid_media_url("https://example.com/with spaces"))

    def test_sanitize_filename(self) -> None:
        self.assertEqual(utils.sanitize_filename('Video: Teste <1> / "Pro"?'), "Video_ Teste _1_ _ _Pro__")
        self.assertEqual(utils.sanitize_filename("CON"), "_CON")
        self.assertEqual(utils.sanitize_filename("   "), "download")

    def test_formatting_helpers(self) -> None:
        self.assertEqual(utils.format_bytes(None), "—")
        self.assertEqual(utils.format_bytes(512 * 1024), "512 KB")
        self.assertEqual(utils.format_speed(2 * 1024 * 1024), "2.0 MB/s")
        self.assertEqual(utils.format_eta(65), "01:05")
        self.assertEqual(utils.format_duration(3661), "1:01:01")

    def test_settings_and_history_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            settings = utils.load_settings(data_dir=tmp_dir)
            settings["max_concurrent"] = 4
            utils.save_settings(settings, data_dir=tmp_dir)

            reloaded = utils.load_settings(data_dir=tmp_dir)
            self.assertEqual(reloaded["max_concurrent"], 4)

            utils.append_history_entry({"title": "Item 1"}, limit=2, data_dir=tmp_dir)
            utils.append_history_entry({"title": "Item 2"}, limit=2, data_dir=tmp_dir)
            hist = utils.append_history_entry({"title": "Item 3"}, limit=2, data_dir=tmp_dir)
            self.assertEqual([h["title"] for h in hist], ["Item 3", "Item 2"])

    def test_create_coffee_logo_and_placeholder(self) -> None:
        logo = utils.create_coffee_logo_image((64, 64))
        self.assertEqual(logo.size, (64, 64))
        thumb = utils.create_placeholder_thumbnail((132, 74), is_audio=True)
        self.assertEqual(thumb.size, (132, 74))
        composited = utils.compose_thumbnail_with_duration(thumb, "03:01")
        self.assertEqual(composited.size, (132, 74))
        icon = utils.create_vector_icon("download", size=16)
        self.assertEqual(icon.size, (16, 16))

    def test_trim_letterbox_bars(self) -> None:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (160, 120), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle((0, 20, 159, 99), fill=(210, 120, 45))
        trimmed = utils._trim_letterbox_bars(img)
        self.assertLess(trimmed.height, 90)
        self.assertGreaterEqual(trimmed.height, 78)

    def test_extract_media_urls_and_queue_persistence(self) -> None:
        raw = "https://youtu.be/abc123\n texto invalido \nhttps://vimeo.com/99999, https://youtu.be/abc123"
        urls = utils.extract_media_urls(raw)
        self.assertEqual(urls, ["https://youtu.be/abc123", "https://vimeo.com/99999"])

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            items = [{"url": "https://youtu.be/1", "title": "Song 1"}]
            utils.save_queue_state(items, data_dir=tmp_dir)
            self.assertEqual(utils.load_queue_state(data_dir=tmp_dir), items)
            utils.save_queue_state([], data_dir=tmp_dir)
            self.assertEqual(utils.load_queue_state(data_dir=tmp_dir), [])

    def test_thread_safe_archive_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "archive.txt"
            threads = [
                threading.Thread(
                    target=lambda idx=i: utils.append_archive_id(f"youtube id_{idx % 5}", archive_path=archive)
                )
                for i in range(20)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            ids = utils.load_archive_ids(archive_path=archive)
            self.assertEqual(len(ids), 5)
            self.assertTrue(utils.is_in_archive("youtube id_3", archive_path=archive))


class TestDownloader(unittest.TestCase):
    def test_build_ydl_options_video_and_audio(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            video_task = downloader.DownloadTask(
                url="https://youtu.be/abc",
                fmt_label=downloader.VIDEO_FORMAT_LABEL,
                quality_label="1080p",
                output_dir=tmp,
            )
            v_opts = downloader.build_ydl_options(
                video_task,
                ratelimit_bps=5 * 1024 * 1024,
                ffmpeg_path="ffmpeg.exe",
            )
            self.assertEqual(
                v_opts["format"],
                "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            )
            self.assertEqual(v_opts["merge_output_format"], "mp4")
            self.assertEqual(v_opts["ratelimit"], 5 * 1024 * 1024)
            self.assertTrue(v_opts["quiet"])
            self.assertTrue(v_opts["no_warnings"])

            audio_task = downloader.DownloadTask(
                url="https://youtu.be/abc",
                fmt_label=downloader.AUDIO_FORMAT_LABEL,
                quality_label="320 kbps (Alta)",
                output_dir=tmp,
                embed_metadata=False,
                cookies_browser="Chrome",
                filename_prefix="01 - ",
            )
            a_opts = downloader.build_ydl_options(audio_task, ffmpeg_path="ffmpeg.exe")
            self.assertEqual(a_opts["format"], "bestaudio/best")
            self.assertEqual(a_opts["cookiesfrombrowser"], ("chrome",))
            self.assertEqual(a_opts["postprocessor_args"], {"extractaudio": ["-compression_level", "7"]})
            self.assertTrue(a_opts["outtmpl"].startswith("01 - "))
            self.assertEqual(a_opts["paths"]["home"], tmp)
            self.assertEqual(
                a_opts["postprocessors"],
                [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
            )

            m4a_task = downloader.DownloadTask(
                url="https://youtu.be/abc",
                fmt_label=downloader.AUDIO_ORIGINAL_FORMAT_LABEL,
                quality_label="Melhor Disponível",
                output_dir=tmp,
                embed_metadata=False,
            )
            m4a_opts = downloader.build_ydl_options(m4a_task, ffmpeg_path="ffmpeg.exe")
            self.assertEqual(m4a_opts["format"], "bestaudio[ext=m4a]/bestaudio/best")
            self.assertEqual(
                m4a_opts["postprocessors"],
                [{"key": "FFmpegExtractAudio", "preferredcodec": "m4a", "preferredquality": "0"}],
            )

    def test_inspect_url_playlist_detection(self) -> None:
        fake_info = {
            "_type": "playlist",
            "title": "Rock Festival",
            "extractor_key": "YoutubeTab",
            "entries": [
                {"id": "vid11111111", "title": "Track 1", "duration": 180},
                {"id": "vid22222222", "title": "Track 2", "duration": 210},
            ],
        }

        class FakeYDL:
            def __init__(self, opts):
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def extract_info(self, url, download=False):
                return fake_info

        mgr = downloader.DownloadManager()
        try:
            with patch("downloader.yt_dlp.YoutubeDL", FakeYDL):
                res = mgr.inspect_url("https://www.youtube.com/watch?v=vid11111111&list=PL123")
            self.assertTrue(res.is_playlist)
            self.assertEqual(res.playlist_title, "Rock Festival")
            self.assertEqual(len(res.entries), 2)
            self.assertEqual(res.single_video_url, "https://www.youtube.com/watch?v=vid11111111")
        finally:
            mgr.shutdown()

    def test_cancel_running_download_triggers_hook_and_cleans_part(self) -> None:
        events: list[str] = []
        done_evt = threading.Event()
        started_evt = threading.Event()

        def on_update(task: downloader.DownloadTask) -> None:
            events.append(task.status)
            if task.status in ("cancelled", "completed", "error"):
                done_evt.set()

        with tempfile.TemporaryDirectory() as tmp:
            part_file = Path(tmp) / "My Video.mp4.part"
            part_file.write_bytes(b"partial")

            class FakeYDL:
                def __init__(self, opts):
                    self.opts = opts

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def extract_info(self, url, download=False):
                    return {"title": "My Video", "duration": 60}

                def prepare_filename(self, info):
                    return str(Path(tmp) / "My Video.mp4")

                def process_ie_result(self, info, download=True):
                    started_evt.set()
                    hook = self.opts["progress_hooks"][0]
                    for _ in range(40):
                        hook({"status": "downloading", "downloaded_bytes": 100, "total_bytes": 1000})
                        time.sleep(0.03)

            mgr = downloader.DownloadManager(max_concurrent=1, on_task_update=on_update)
            try:
                task = downloader.DownloadTask(
                    url="https://youtu.be/cancelme",
                    fmt_label=downloader.VIDEO_FORMAT_LABEL,
                    quality_label="1080p",
                    output_dir=tmp,
                )
                with patch("downloader.yt_dlp.YoutubeDL", FakeYDL):
                    mgr.enqueue(task)
                    self.assertTrue(started_evt.wait(timeout=3.0))
                    mgr.cancel_task(task.task_id)
                    self.assertTrue(done_evt.wait(timeout=3.0))

                self.assertEqual(task.status, "cancelled")
                self.assertFalse(part_file.exists())
            finally:
                mgr.shutdown()

    def test_dynamic_concurrency_limit_respected(self) -> None:
        max_observed = 0
        current_running = 0
        lock = threading.Lock()
        all_done = threading.Event()
        completed_count = 0

        def on_update(task: downloader.DownloadTask) -> None:
            nonlocal completed_count
            if task.status == "completed":
                with lock:
                    completed_count += 1
                    if completed_count == 3:
                        all_done.set()

        with tempfile.TemporaryDirectory() as tmp:
            class FakeYDL:
                def __init__(self, opts):
                    self.opts = opts

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def extract_info(self, url, download=False):
                    return {"title": "Clip", "duration": 10}

                def prepare_filename(self, info):
                    return str(Path(tmp) / "Clip.mp4")

                def process_ie_result(self, info, download=True):
                    nonlocal max_observed, current_running
                    with lock:
                        current_running += 1
                        max_observed = max(max_observed, current_running)
                    time.sleep(0.08)
                    with lock:
                        current_running -= 1

            mgr = downloader.DownloadManager(max_concurrent=1, on_task_update=on_update)
            try:
                with patch("downloader.yt_dlp.YoutubeDL", FakeYDL):
                    for idx in range(3):
                        mgr.enqueue(
                            downloader.DownloadTask(
                                url=f"https://youtu.be/vid{idx}",
                                fmt_label=downloader.VIDEO_FORMAT_LABEL,
                                quality_label="720p",
                                output_dir=tmp,
                            )
                        )
                    self.assertTrue(all_done.wait(timeout=5.0))
                self.assertEqual(max_observed, 1)
            finally:
                mgr.shutdown()

    def test_skip_existing_file_and_ten_worker_limit(self) -> None:
        done_evt = threading.Event()

        def on_update(task: downloader.DownloadTask) -> None:
            if task.status in ("skipped", "completed", "error"):
                done_evt.set()

        with tempfile.TemporaryDirectory() as tmp:
            existing = Path(tmp) / "Ja Baixada.mp3"
            existing.write_bytes(b"fake mp3 bytes")

            class FakeYDL:
                def __init__(self, opts):
                    self.opts = opts

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

                def extract_info(self, url, download=False):
                    return {"id": "abc123", "title": "Ja Baixada", "duration": 180}

                def prepare_filename(self, info):
                    return str(Path(tmp) / "Ja Baixada.webm")

                def in_download_archive(self, info):
                    return False

                def process_ie_result(self, info, download=True):
                    raise AssertionError("Nao deveria baixar quando o arquivo ja existe")

            mgr = downloader.DownloadManager(max_concurrent=10, on_task_update=on_update)
            self.assertEqual(mgr.max_concurrent, 10)
            try:
                task = downloader.DownloadTask(
                    url="https://youtu.be/abc123",
                    fmt_label=downloader.AUDIO_FORMAT_LABEL,
                    quality_label="320 kbps (Alta)",
                    output_dir=tmp,
                    skip_existing=True,
                    archive_file=str(Path(tmp) / "archive.txt"),
                )
                with patch("downloader.yt_dlp.YoutubeDL", FakeYDL):
                    mgr.enqueue(task)
                    self.assertTrue(done_evt.wait(timeout=3.0))

                self.assertEqual(task.status, "skipped")
                self.assertEqual(task.progress, 1.0)
            finally:
                mgr.shutdown()

    def test_cookies_file_and_error_formatting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cookies_path = Path(tmp) / "cookies.txt"
            cookies_path.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")

            task = downloader.DownloadTask(
                url="https://youtu.be/age18",
                fmt_label=downloader.VIDEO_FORMAT_LABEL,
                quality_label="1080p",
                output_dir=tmp,
                cookies_browser="Chrome",
                cookies_file=str(cookies_path),
            )
            opts = downloader.build_ydl_options(task, ffmpeg_path="ffmpeg.exe")
            self.assertTrue(opts["no_color"])
            self.assertEqual(opts["cookiefile"], str(cookies_path))
            self.assertNotIn("cookiesfrombrowser", opts)

        age_msg = downloader.DownloadManager._format_error(
            RuntimeError("\x1b[0;31mERROR:\x1b[0m [youtube] Ei1XHqaaFmI: Sign in to confirm your age.")
        )
        self.assertIn("Vídeo +18", age_msg)
        self.assertNotIn("\x1b", age_msg)
        self.assertNotIn("[0m", age_msg)

        lock_msg = downloader.DownloadManager._format_error(
            RuntimeError("\x1b[0mERROR: Could not copy Chrome cookie database")
        )
        self.assertIn("cookies.txt", lock_msg)
        self.assertNotIn("\x1b", lock_msg)

        plain_msg = downloader.DownloadManager._format_error(
            RuntimeError("\x1b[0;31mERROR:\x1b[0m [youtube] Video unavailable")
        )
        self.assertEqual(plain_msg, "[youtube] Video unavailable")


if __name__ == "__main__":
    unittest.main()
