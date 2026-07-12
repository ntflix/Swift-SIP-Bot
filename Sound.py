class Sound:
    title: str
    description: str
    url: str

    def __init__(self, title: str, description: str, url: str):
        self.title = title
        self.description = description
        self.url = url

    def get_download_path(self) -> str:
        """
        Extracts the filename from the URL for downloading.
        """
        return self.url.split("/")[-1]

    @staticmethod
    def load_sounds_from_json(json_path: str) -> list["Sound"]:
        import json

        with open(json_path, "r") as f:
            data = json.load(f)
            return [Sound(**item) for item in data]
