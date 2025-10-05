# Imports and libraries
import asf_search as asf
import hyp3_sdk
from pathlib import Path
from zipfile import ZipFile
import Crop_Product as cp
import subprocess
import configparser
import padding
import Normalize
import tifCheck
import shutil


def getFinalPatchDir():
    #Initiation:
    config = configparser.ConfigParser()
    config.read('config.ini')
    start_date=config.get('Other','start_date')
    end_date=config.get('Other','end_date')    
    usr = config.get('Login','user')
    pas = config.get('Login','password')
    wkt = config.get('Other','wkt')
    n = config.getint('Other','index_of_product')    
    loc=config.get('Other','store_location')
    lakeName = config.get('Other', 'lakeName').split(', ')
    years = config.get('Other', 'years').split(', ')
    job_name = config.get('Other','job_name')
    before_norm = config.get('Other','before_norm')
    after_norm = config.get('Other','after_norm')
    print("We are working on lake: ",lakeName)

    #hyp3 authentication
    hyp3 = hyp3_sdk.HyP3(username=usr, password=pas)

    #Searching:

    results = []
    for year in years:
        results_thisYear = asf.geo_search(intersectsWith=wkt,
                                platform=[asf.PLATFORM.SENTINEL1],
                                processingLevel=[asf.PRODUCT_TYPE.GRD_HD,asf.PRODUCT_TYPE.GRD_HS, asf.PRODUCT_TYPE.GRD_MD, asf.PRODUCT_TYPE.GRD_MS, asf.PRODUCT_TYPE.GRD_FD],
                                start=year + '-' + start_date,
                                end=year + '-' + end_date)
        try: 
            results.append(results_thisYear[n])
        except IndexError:
            print(f"Didn't file product for year {year}.")



    granule_ids = [result.properties['sceneName'] for result in results]

    #Display found products
    for result in results:
        print(result)

    # Prepare RTC jobs from products
    jobs = hyp3.find_jobs(name=job_name)

    if not jobs:
        print("No existing jobs found. Preparing new RTC jobs from products.")
        job_definitions = []
        for granule_id in granule_ids:
            job_definitions.append(
                hyp3.prepare_rtc_job(  
                        granule_id, 
                        name=job_name,
                        speckle_filter= True,
                        resolution=20,
                    )
            )
        print(job_definitions)
        
        check = input("Do you want to continue to processing? (Y/N)")
        try:
            if check.lower() == 'y':
                jobs = hyp3.submit_prepared_jobs(job_definitions)
        except:
            print("Enter either 'y' or 'Y' if you want to continue submission.")
    else:
        print(f"Found {len(jobs)} existing jobs with name '{job_name}'.")
        check = input("Do you want to skip submission and start watching the existing job(s)? (Y/N) ")
        if check.lower() != 'y':
            print("Proceeding to submit new jobs as requested.")
            job_definitions = []
            for granule_id in granule_ids:
                job_definitions.append(
                    hyp3.prepare_rtc_job(  
                            granule_id, 
                            name=job_name,
                            speckle_filter= True,
                            resolution=20,
                        )
                )
            print(job_definitions)
            jobs = hyp3.submit_prepared_jobs(job_definitions)

    #Check and continue with processing
    print("Watching jobs...")
    jobs = hyp3.watch(jobs)
    
    jobs_urls = [job.files[0]['url'] for job in jobs if job.succeeded()]
    if not jobs_urls:
        print("No successful jobs found to download.")
        return None
    
    print("Download URLs:", jobs_urls)

    #Check and continue with downloading
    Path(loc).mkdir(exist_ok=True)
    for url in jobs_urls:
        subprocess.run(["wget", "-c", url, "-P", loc])
        #job.download_files(location = loc, create=True)

    #Preparing to unzip
    zipPaths = []
    for path in Path(loc).glob("*.zip"):
        zipPaths.append(path)


    for zipPath in zipPaths:
        zipName = zipPath.name
        #if pattern.match(zipName):
        print(zipName)
        tifName = zipName.replace(".zip","")+'/'+zipName.replace(".zip","_VV.tif")

        try:
            with ZipFile(zipPath, 'r') as zObj:
                print(zObj.namelist())
                zObj.extract(tifName, path=loc)
            zObj.close()

            tifPath = Path(f'{loc}/{tifName}')
            lakePath = f'../Lakes_Patches/{lakeName}'
            Path('../Lakes_Patches').mkdir(exist_ok=True)
            Path(lakePath).mkdir(exist_ok=True)
            crop_out=cp.crop(tifPath, wkt, lakePath, lakeName)
            padded_out = lakePath + f'/Padded/{crop_out.name}'
            Path(f'{lakePath}/Padded').mkdir(exist_ok=True)
            padding.pad_and_save_tif(str(crop_out), padded_out)
            Path(before_norm).mkdir(exist_ok=True)
            shutil.copy(padded_out, before_norm)
        except:
            print("Couldn't extract the zip: ", zipName)

    finalOut = Normalize.normalize(before_norm,after_norm)
    tifCheck.finalCheck(finalOut)

    return finalOut

