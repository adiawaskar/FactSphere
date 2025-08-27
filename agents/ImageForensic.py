# import os
# import json
# import uuid
# from datetime import datetime, timezone
# from PIL import Image, ImageChops, ImageEnhance, ExifTags

# # ---------- EXIF Extraction ----------
# def exif_from_pillow(path):
#     img = Image.open(path)
#     exif = img.getexif()
#     if not exif:
#         return {}
#     data = {}
#     for tag_id, val in exif.items():
#         tag = ExifTags.TAGS.get(tag_id, str(tag_id))
#         data[tag] = val
#     # GPS info
#     gps_tag = None
#     for k, v in ExifTags.TAGS.items():
#         if v == "GPSInfo":
#             gps_tag = k
#             break
#     if gps_tag and gps_tag in exif:
#         gps_raw = exif.get(gps_tag)
#         gps = {}
#         for t_id, t_val in gps_raw.items():
#             gps_name = ExifTags.GPSTAGS.get(t_id, str(t_id))
#             gps[gps_name] = t_val
#         data["GPSInfo"] = gps
#     return safe_exif_to_jsonable(data)

# def safe_exif_to_jsonable(d):
#     def conv(v):
#         if isinstance(v, bytes):
#             try:
#                 return v.decode("utf-8", "ignore")
#             except:
#                 return repr(v)
#         if isinstance(v, (tuple, list)):
#             return [conv(x) for x in v]
#         if isinstance(v, dict):
#             return {str(k): conv(v2) for k, v2 in v.items()}
#         try:
#             json.dumps(v)
#             return v
#         except:
#             return str(v)
#     return {k: conv(v) for k, v in d.items()}

# def gps_to_deg(gpsinfo):
#     if not gpsinfo:
#         return None
#     try:
#         def to_deg(x):
#             a = x[0][0] / x[0][1]
#             b = x[1][0] / x[1][1]
#             c = x[2][0] / x[2][1]
#             return a + b / 60 + c / 3600
#         lat_ref = gpsinfo.get("GPSLatitudeRef")
#         lon_ref = gpsinfo.get("GPSLongitudeRef")
#         lat = gpsinfo.get("GPSLatitude")
#         lon = gpsinfo.get("GPSLongitude")
#         if not (lat_ref and lon_ref and lat and lon):
#             return None
#         lat_d = to_deg(lat) * (1 if lat_ref in ["N", "n"] else -1)
#         lon_d = to_deg(lon) * (1 if lon_ref in ["E", "e"] else -1)
#         return {"lat": lat_d, "lon": lon_d}
#     except:
#         return None

# # ---------- Date Parsing ----------
# def exif_datetime_candidates(exif):
#     keys = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]
#     vals = []
#     for k in keys:
#         v = exif.get(k)
#         if isinstance(v, str):
#             vals.append(v)
#     for v in vals:
#         dt = try_parse_exif_datetime(v)
#         if dt:
#             return dt
#     return None

# def try_parse_exif_datetime(s):
#     s2 = s.strip().replace("-", ":").replace(".", ":")
#     fmts = ["%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M", "%Y:%m:%d"]
#     for f in fmts:
#         try:
#             return datetime.strptime(s2, f).replace(tzinfo=timezone.utc)
#         except:
#             pass
#     return None

# # ---------- Error Level Analysis ----------
# def ela_image(path, out_dir, quality=90):
#     img = Image.open(path).convert("RGB")
#     temp = os.path.join(out_dir, f"ela_tmp_{uuid.uuid4().hex}.jpg")
#     img.save(temp, "JPEG", quality=quality)
#     comp = Image.open(temp)
#     diff = ImageChops.difference(img, comp)
#     extrema = diff.getextrema()
#     max_diff = max(e[1] for e in extrema) or 1
#     scale = 255.0 / max_diff
#     ela = ImageEnhance.Brightness(diff).enhance(scale)
#     out = os.path.join(out_dir, f"ela_{os.path.basename(path)}.png")
#     ela.save(out)
#     try:
#         os.remove(temp)
#     except:
#         pass
#     return out

# # ---------- Anomaly Checks ----------
# def anomaly_checks(exif):
#     issues = []
#     if not exif:
#         issues.append("no_exif_metadata")
#         return issues
#     exif_dt = exif_datetime_candidates(exif)
#     gps = gps_to_deg(exif.get("GPSInfo"))
#     if exif.get("Software") and isinstance(exif["Software"], str) and any(
#         x in exif["Software"].lower() for x in ["photoshop", "gimp", "canva", "snapseed", "lightroom"]
#     ):
#         issues.append("edited_software_detected")
#     return issues

# # ---------- Main Local Image Analyzer ----------
# def analyze_local_images(image_paths, workdir="media_audit"):
#     os.makedirs(workdir, exist_ok=True)
#     img_dir = os.path.join(workdir, "images")
#     ela_dir = os.path.join(workdir, "ela")
#     os.makedirs(img_dir, exist_ok=True)
#     os.makedirs(ela_dir, exist_ok=True)

#     results = []
#     for path in image_paths:
#         try:
#             exif = exif_from_pillow(path)
#             ela_path = ela_image(path, ela_dir)
#             issues = anomaly_checks(exif)
#             gps = gps_to_deg(exif.get("GPSInfo")) if exif else None
#             exif_dt = exif_datetime_candidates(exif) if exif else None
#             results.append({
#                 "local_path": path,
#                 "ela_path": ela_path,
#                 "exif_summary": {
#                     "camera_model": exif.get("Model"),
#                     "make": exif.get("Make"),
#                     "datetime_original": exif.get("DateTimeOriginal") or exif.get("DateTime"),
#                     "software": exif.get("Software"),
#                     "gps": gps
#                 },
#                 "issues": issues,
#                 "parsed_dates": {
#                     "exif_datetime": exif_dt.isoformat() if exif_dt else None
#                 }
#             })
#         except Exception as e:
#             results.append({"local_path": path, "error": str(e)})
#     return {"image_count": len(image_paths), "results": results, "output_dirs": {"images_dir": img_dir, "ela_dir": ela_dir}}

# # ---------- Run from CLI ----------
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print(json.dumps({"error": "usage: python media_verify_local.py <image1> <image2> ..."}))
#         sys.exit(1)
#     image_paths = sys.argv[1:]
#     report = analyze_local_images(image_paths)
#     print(json.dumps(report, indent=2))

import os
import json
import uuid
from datetime import datetime, timezone
from PIL import Image, ImageChops, ImageEnhance, ExifTags

# ---------- EXIF Extraction ----------
def exif_from_pillow(path):
    """
    Extracts EXIF metadata from an image using Pillow.

    Args:
        path (str): The file path to the image.

    Returns:
        dict: A dictionary containing EXIF data, or an empty dictionary if no EXIF data is found.
    """
    img = Image.open(path)
    exif = img.getexif()
    if not exif:
        return {}
    
    data = {}
    for tag_id, val in exif.items():
        # Get the human-readable tag name, fallback to string representation of ID
        tag = ExifTags.TAGS.get(tag_id, str(tag_id))
        data[tag] = val

    # Extract and format GPS info if available
    gps_tag_id = None
    for k, v in ExifTags.TAGS.items():
        if v == "GPSInfo":
            gps_tag_id = k
            break
    
    if gps_tag_id and gps_tag_id in exif:
        gps_raw = exif.get(gps_tag_id)
        gps = {}
        for t_id, t_val in gps_raw.items():
            gps_name = ExifTags.GPSTAGS.get(t_id, str(t_id))
            gps[gps_name] = t_val
        data["GPSInfo"] = gps
        
    return safe_exif_to_jsonable(data)

def safe_exif_to_jsonable(d):
    """
    Converts EXIF dictionary values into JSON-serializable types.
    Handles bytes, tuples, lists, and dicts.

    Args:
        d (dict): The dictionary of EXIF data.

    Returns:
        dict: EXIF data with values converted to JSON-compatible types.
    """
    def conv(v):
        if isinstance(v, bytes):
            try:
                # Attempt to decode bytes to UTF-8, ignore errors
                return v.decode("utf-8", "ignore")
            except:
                # Fallback to string representation if decoding fails
                return repr(v)
        if isinstance(v, (tuple, list)):
            return [conv(x) for x in v]
        if isinstance(v, dict):
            return {str(k): conv(v2) for k, v2 in v.items()}
        
        # Try to directly serialize, otherwise convert to string
        try:
            json.dumps(v)
            return v
        except:
            return str(v)
            
    return {k: conv(v) for k, v in d.items()}

def gps_to_deg(gpsinfo):
    """
    Converts raw GPS EXIF data to decimal degrees (latitude, longitude).

    Args:
        gpsinfo (dict): The 'GPSInfo' dictionary from EXIF data.

    Returns:
        dict: A dictionary with 'lat' and 'lon' in decimal degrees, or None if conversion fails.
    """
    if not gpsinfo:
        return None
    try:
        def to_deg(x):
            # Converts GPS rational (numerator, denominator) to float
            return x[0] / x[1] if x[1] != 0 else 0.0

        # Extract latitude and longitude components
        lat_ref = gpsinfo.get("GPSLatitudeRef")
        lon_ref = gpsinfo.get("GPSLongitudeRef")
        lat_raw = gpsinfo.get("GPSLatitude")
        lon_raw = gpsinfo.get("GPSLongitude")

        if not (lat_ref and lon_ref and lat_raw and lon_raw and len(lat_raw) == 3 and len(lon_raw) == 3):
            return None

        # Convert degrees, minutes, seconds to decimal
        lat_d = to_deg(lat_raw[0]) + to_deg(lat_raw[1]) / 60 + to_deg(lat_raw[2]) / 3600
        lon_d = to_deg(lon_raw[0]) + to_deg(lon_raw[1]) / 60 + to_deg(lon_raw[2]) / 3600

        # Apply reference (N/S, E/W) for correct sign
        lat_d *= (1 if lat_ref in ["N", "n"] else -1)
        lon_d *= (1 if lon_ref in ["E", "e"] else -1)
        
        return {"lat": lat_d, "lon": lon_d}
    except Exception as e:
        print(f"Error converting GPS to degrees: {e}")
        return None

# ---------- Date Parsing ----------
def exif_datetime_candidates(exif):
    """
    Attempts to parse a datetime object from common EXIF date fields.

    Args:
        exif (dict): The EXIF data dictionary.

    Returns:
        datetime.datetime: A datetime object with UTC timezone, or None if no valid date is found.
    """
    keys = ["DateTimeOriginal", "DateTimeDigitized", "DateTime"]
    vals = []
    for k in keys:
        v = exif.get(k)
        if isinstance(v, str):
            vals.append(v)
            
    for v in vals:
        dt = try_parse_exif_datetime(v)
        if dt:
            return dt
    return None

def try_parse_exif_datetime(s):
    """
    Tries to parse an EXIF date string into a datetime object using various formats.

    Args:
        s (str): The date string from EXIF.

    Returns:
        datetime.datetime: A timezone-aware datetime object, or None if parsing fails.
    """
    s2 = s.strip().replace("-", ":").replace(".", ":")
    # Common EXIF date formats
    fmts = ["%Y:%m:%d %H:%M:%S", "%Y:%m:%d %H:%M", "%Y:%m:%d"]
    for f in fmts:
        try:
            return datetime.strptime(s2, f).replace(tzinfo=timezone.utc)
        except ValueError:
            pass # Try next format
    return None

# ---------- Error Level Analysis ----------
def ela_image(path, out_dir, quality=90):
    """
    Performs Error Level Analysis (ELA) on an image.
    Saves the ELA result as a PNG in the specified output directory.

    Args:
        path (str): Path to the input image.
        out_dir (str): Directory to save the ELA image.
        quality (int): JPEG quality setting for re-compression (default: 90).

    Returns:
        str: Path to the saved ELA image.
    """
    try:
        # Open original image and convert to RGB (for JPEG saving)
        img = Image.open(path).convert("RGB")
        
        # Create a temporary file path for the re-compressed image
        temp_filename = f"ela_tmp_{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join(out_dir, temp_filename)
        
        # Save the image at a specified quality, then reopen
        img.save(temp_path, "JPEG", quality=quality)
        comp = Image.open(temp_path)
        
        # Calculate the difference between original and re-compressed
        diff = ImageChops.difference(img, comp)
        
        # Enhance the difference image to make error levels more visible
        extrema = diff.getextrema()
        # Find the maximum difference value across all bands
        max_diff = max(e[1] for e in extrema) if extrema else 1
        scale = 255.0 / max_diff if max_diff > 0 else 1.0
        ela = ImageEnhance.Brightness(diff).enhance(scale)
        
        # Save the ELA image as PNG
        output_filename = f"ela_{os.path.basename(path)}.png"
        out_path = os.path.join(out_dir, output_filename)
        ela.save(out_path)
        
        return out_path
    except Exception as e:
        print(f"Error during ELA for {path}: {e}")
        return None
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"Error removing temporary ELA file {temp_path}: {e}")

# ---------- Anomaly Checks ----------
def anomaly_checks(exif):
    """
    Performs basic anomaly checks based on EXIF metadata.

    Args:
        exif (dict): The EXIF data dictionary.

    Returns:
        list: A list of strings, each indicating a detected issue.
    """
    issues = []
    if not exif:
        issues.append("no_exif_metadata")
        return issues

    # Check for known photo editing software in the 'Software' tag
    software_field = exif.get("Software")
    if software_field and isinstance(software_field, str):
        editing_software_keywords = ["photoshop", "gimp", "canva", "snapseed", "lightroom", "picsart"]
        if any(x in software_field.lower() for x in editing_software_keywords):
            issues.append("edited_software_detected")
            
    # Add more anomaly checks here as needed
    # Example: Check if DateTimeOriginal is significantly later than DateTimeDigitized

    return issues

# ---------- Main Local Image Analyzer ----------
def analyze_local_images(image_paths, workdir="media_audit"):
    """
    Analyzes a list of local image files for EXIF metadata, ELA, and anomalies.

    Args:
        image_paths (list): A list of file paths to images.
        workdir (str): The base directory to store output (ELA images, etc.).

    Returns:
        dict: A report containing analysis results for each image.
    """
    # Create necessary output directories
    os.makedirs(workdir, exist_ok=True)
    img_dir = os.path.join(workdir, "processed_images") # Not strictly used, but good for organization
    ela_dir = os.path.join(workdir, "ela_results")
    os.makedirs(img_dir, exist_ok=True) # Ensure this exists
    os.makedirs(ela_dir, exist_ok=True)

    results = []
    for path in image_paths:
        file_result = {"local_path": path}
        try:
            # Extract EXIF data
            exif = exif_from_pillow(path)
            
            # Perform Error Level Analysis
            ela_output_path = ela_image(path, ela_dir)
            
            # Perform anomaly checks
            issues = anomaly_checks(exif)
            
            # Parse GPS and datetime
            gps_data = gps_to_deg(exif.get("GPSInfo")) if exif else None
            exif_datetime_parsed = exif_datetime_candidates(exif) if exif else None

            file_result.update({
                "ela_path": ela_output_path,
                "exif_summary": {
                    "camera_model": exif.get("Model", "N/A"),
                    "make": exif.get("Make", "N/A"),
                    "datetime_original_raw": exif.get("DateTimeOriginal", exif.get("DateTime", "N/A")),
                    "software": exif.get("Software", "N/A"),
                    "gps_coordinates": gps_data
                },
                "issues": issues,
                "parsed_dates": {
                    "exif_datetime_utc": exif_datetime_parsed.isoformat() if exif_datetime_parsed else None
                }
            })
        except Exception as e:
            file_result["error"] = f"Failed to process image: {e}"
            print(f"Error processing {path}: {e}") # Print error to console for immediate feedback
        finally:
            results.append(file_result)

    return {
        "image_count": len(image_paths), 
        "results": results, 
        "output_dirs": {
            "analysis_report_dir": workdir,
            "ela_images_dir": ela_dir
        }
    }

# ---------- Run from CLI (now uses a static input folder) ----------
if __name__ == "__main__":
    # Define the static input folder
    INPUT_FOLDER = "/Users/keshavdhanuka01/Desktop/MisinfoVerify/FactSphere/Images"
    os.makedirs(INPUT_FOLDER, exist_ok=True) # Create the input folder if it doesn't exist

    print(f"Scanning for images in the '{INPUT_FOLDER}/' directory...")
    
    image_paths_to_analyze = []
    # Define common image extensions
    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')

    for filename in os.listdir(INPUT_FOLDER):
        if filename.lower().endswith(IMAGE_EXTENSIONS):
            full_path = os.path.join(INPUT_FOLDER, filename)
            image_paths_to_analyze.append(full_path)

    if not image_paths_to_analyze:
        print(f"No image files found in the '{INPUT_FOLDER}/' directory. Please place your images there.")
        print(json.dumps({"error": f"No images found in {INPUT_FOLDER}"}, indent=2))
        sys.exit(1)

    print(f"Found {len(image_paths_to_analyze)} image(s) to analyze.")
    report = analyze_local_images(image_paths_to_analyze)
    
    # Save the report to a file for easier viewing
    report_filename = os.path.join(report["output_dirs"]["analysis_report_dir"], "image_analysis_report.json")
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nAnalysis complete! Report saved to '{report_filename}'.")
    print(f"ELA images saved to '{report['output_dirs']['ela_images_dir']}'.")
    print("\n" + json.dumps(report, indent=2, ensure_ascii=False))

