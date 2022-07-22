from gooddata_sdk import GoodDataSdk
from pathlib import Path
import os

layouts_path = Path("")
credentials_path = Path("./credentials.yaml")
host = os.environ.get("HOST", "http://localhost:3000")
token = os.environ.get("TOKEN", "YWRtaW46Ym9vdHN0cmFwOmFkbWluMTIz")
header_host = os.environ.get("HEADER_HOST", "localhost")


def upload_data():
    sdk = GoodDataSdk.create(host_=host, token_=token, Host=header_host)

    # Wait for the GoodData.CN docker image to start up
    print(f"Waiting for {host} to be up.", flush=True)
    sdk.support.wait_till_available(timeout=-1)
    print(f"Host {host} is up.", flush=True)

    # When the GoodData.CN docker image is ready upload data
    print("Upload layouts.", flush=True)
    sdk.catalog_data_source.load_and_put_declarative_data_sources(layouts_path, credentials_path=credentials_path)
    sdk.catalog_workspace.load_and_put_declarative_workspaces(layouts_path)
    print("Done.", flush=True)


if __name__ == "__main__":
    upload_data()
