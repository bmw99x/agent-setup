# Restrict document uploads

Users are uploading huge files and file types the app can't display. Update `upload_document` in `/app/app/documents/service.py` so that it:

- rejects files larger than 25 MB, and
- rejects any file type our document preview doesn't support.

Rejections should raise the existing `UploadRejected` (`app/documents/errors.py`). Its message is shown to the user as-is, so it should tell them what the limit is or which file types are allowed.
