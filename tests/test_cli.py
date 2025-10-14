import pytest
from unittest.mock import patch, mock_open
from BlenderUpdaterCLI import (
    parse_arguments,
    check_for_app_update,
    process_settings,
    download_file,
    extract_archive,
    copy_files,
    cleanup,
    main
)

@pytest.fixture
def mock_args(tmp_path):
    return [
        "-p",
        str(tmp_path),
        "-b",
        "3.0.0",
        "-o",
        "windows",
    ]


def test_parse_arguments(mock_args):
    with patch("sys.argv", ["BlenderUpdaterCLI.py"] + mock_args):
        args = parse_arguments()
        assert args.path is not None
        assert args.blender == "3.0.0"
        assert args.operatingsystem == "windows"


@patch("requests.get")
def test_check_for_app_update_no_update(mock_get):
    mock_get.return_value.text = '{"tag_name": "v1.7.1"}'
    with patch("sys.exit") as mock_exit:
        check_for_app_update()
        mock_exit.assert_not_called()


@patch("requests.get")
def test_check_for_app_update_new_version(mock_get):
    mock_get.return_value.text = '{"tag_name": "v2.0.0"}'
    with patch("sys.exit") as mock_exit:
        check_for_app_update()
        mock_exit.assert_called_with(1)


@patch("platform.system", return_value="Windows")
def test_process_settings(mock_system, tmp_path):
    class Args:
        path = str(tmp_path)
        blender = "3.0.0"
        operatingsystem = None
        temp = None
        keep = False
        run = False
        yes = False
        no = False

    args = Args()
    settings = process_settings(args)
    assert settings["destination_path"] == str(tmp_path)
    assert settings["blender"] == "3.0.0"
    assert settings["opsys"] == "windows"


@patch("requests.get")
@patch("progress.bar.IncrementalBar")
def test_download_file(mock_bar, mock_get, tmp_path):
    mock_get.return_value.headers = {"Content-Length": "10240"}
    mock_get.return_value.iter_content.return_value = [b"test"] * 1024
    download_path = download_file("http://test.com/", "test.zip", str(tmp_path))
    assert download_path is not None
    assert (tmp_path / "test.zip").exists()


@patch("shutil.unpack_archive")
def test_extract_archive(mock_unpack, tmp_path):
    result = extract_archive("test.zip", str(tmp_path))
    assert result is True
    mock_unpack.assert_called_with("test.zip", str(tmp_path))


    @patch("shutil.copytree")
    @patch("os.walk")
    def test_copy_files(mock_walk, mock_copytree, tmp_path):
        mock_walk.return_value = iter([("", ["test_dir"], [])])
        result = copy_files(str(tmp_path), "dest_path")
        assert result is True
        mock_copytree.assert_called_with(str(tmp_path / "test_dir"), "dest_path", dirs_exist_ok=True)

@patch("shutil.rmtree")
def test_cleanup(mock_rmtree, tmp_path):
    result = cleanup(False, str(tmp_path))
    assert result is True
    mock_rmtree.assert_called_with(str(tmp_path))


@patch("BlenderUpdaterCLI.parse_arguments")
@patch("BlenderUpdaterCLI.check_for_app_update")
@patch("BlenderUpdaterCLI.process_settings")
@patch("requests.get")
@patch("re.findall")
@patch("os.path.isfile")
@patch("builtins.input", return_value="y")
@patch("os.makedirs")
@patch("BlenderUpdaterCLI.download_file")
@patch("BlenderUpdaterCLI.extract_archive")
@patch("BlenderUpdaterCLI.copy_files")
@patch("BlenderUpdaterCLI.cleanup")
@patch("configparser.ConfigParser")
@patch("subprocess.Popen")
def test_main(mock_popen, mock_config, mock_cleanup, mock_copy, mock_extract, mock_download, mock_makedirs, mock_input, mock_isfile, mock_findall, mock_requests_get, mock_process_settings, mock_check_update, mock_parse_args, tmp_path):
    class Args:
        path = str(tmp_path)
        blender = "3.0.0"
        operatingsystem = "windows"
        temp = None
        keep = False
        run = True
        yes = False
        no = False

    mock_parse_args.return_value = Args()
    mock_process_settings.return_value = {
        "destination_path": str(tmp_path),
        "tempDir": "temp",
        "blender": "3.0.0",
        "opsys": "windows",
        "extension": "zip",
        "keep_temp": False,
        "will_run": True,
    }
    mock_requests_get.return_value.text = "blender-3.0.0-windows-x64.zip"
    mock_findall.return_value = ["blender-3.0.0-windows-x64.zip"]
    mock_isfile.return_value = True
    mock_download.return_value = "temp/blender-3.0.0-windows-x64.zip"
    mock_extract.return_value = True
    mock_copy.return_value = True
    mock_cleanup.return_value = True

    with patch("sys.argv", ["BlenderUpdaterCLI.py", "-p", str(tmp_path), "-b", "3.0.0", "-r"]):
        main()

    mock_popen.assert_called_once()
