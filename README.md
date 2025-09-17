## Get My API Data
A GUI tool for querying All of Us participant data using the InSite API.

![image_info](./pictures/generic_gui.png)

### Installation

1. Install [`gcloud tools`](https://cloud.google.com/sdk/docs/install)
2. Download the `.exe` version of this app from [GitHub](https://github.com/DBMI/GetMyApiData/releases/tag/v0.1-exe)
3. Run `GetMyApiData.exe`

### Operation
Once you've inserted into the GUI your actual PMI account and service account information and selected the location for the `key.json` file, press `Request Data`.

The gcloud account selection page will appear:

![image_info](./pictures/choose_the_form.png)

... and request permission to access your account:

![image_info](./pictures/ok_to_access.png)

... and finally show you're authenticated:

![image_info](./pictures/authenticated.png)

Once the files have been downloaded, the app will ask you to specify a folder in which to save them. The folder will contain your participant list in both InSite format and transformed into the HealthPro format (to accommodate legacy code):

![image_info](./pictures/data_directory.png)


### Support
Contact Kevin J. Delaney at UC San Diego: <kjdelaney@health.ucsd.edu>
