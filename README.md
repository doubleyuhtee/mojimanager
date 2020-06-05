# Moji Manager

For copying emoji from your slack workspace and bulk uploading folders.

## Modes

### Collect

Fetch the listing of the custom emoji in the workspace corresponding to the api key provided and download all images to a folder.  Each file name is taken from the emoji name.  Aliases are not handled.

#### Args

* --token (String, required) - api key
* --collect (no arg) - enable this mode
* --workspace, -w (String, default: 'default') - folder name to write summary and images to

#### Sample

`python manage.py --token xoxp-******** --collect --workspace my_data`

`python manage.py --collect --workspace teamname`

### Create

Upload all images in a given folder to the workspace corresponding to the api key provided use the file name as the emoji name.

#### Args

* --token (String, required) - api key needs to be sniffed from the web ui
* --create (String, required) - path to the folder to upload.
* --batch_size (int, default: 10) - Number of files to upload before sleeping.  This is to prevent rate limiting.

#### Sample

`python manage.py --token xoxs-********* --create data/sample/`


##Token
To get your xoxs-##### token for uploading, open the customize page in your browser, open the networking tab in the developer pane, and find a request with the token included (emoji.list for example)