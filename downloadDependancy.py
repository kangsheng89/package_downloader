import os
import sys
import json
from datetime import datetime
import subprocess
from multiprocessing.pool import ThreadPool

json_file="dependencies.json"
dependancies_folder = "D://dependencies//"

def _main():

    data, list_name, path_list, date_list, size_list = ReadJson(json_file)
    initial, empty_folder, dict_obj = CheckFolder(dependancies_folder)
    count, tool_index, path_to_download, datetime_list, size_list = CheckDateTime(date_list,path_list, dict_obj)
    UpdateJson(json_file, data, count, tool_index, list_name, datetime_list, size_list)
    
    if (initial is True) or (empty_folder is True):
        #download all from json file
        status = run_downloader(path_list,dependancies_folder)
        if (status==0):
            print("Download Completed")
        else:
            sys.exit(1)

    else:

        if len(path_to_download)==0:
            print("Latest Dependancies")
            sys.exit(0)
        else:
            print("update in progress")
            #delete zip
            #using set instead of list to prevent download from same path
            DeleteOldZipped(set(path_to_download), dependancies_folder)
            #update by re-downloading
            status = run_downloader(set(path_to_download),dependancies_folder)
            if (status==0):
                print("Download Completed")
            else:
                sys.exit(1)
        
    sys.exit(0)


def ReadJson(json_file):
    list_name=[]
    path_list=[]
    date_list=[]
    size_list=[]
    jsonfile = open(json_file, "r")
    data = json.load(jsonfile)
    jsonfile.close()
    for x in data:
        list_name.append(x)
        for k,v in data[x].items():
            if "path" in k:
                path_list.append(v)
            if "lastModified" in k:
                datetime_obj = datetime.strptime(v, "%a, %d %b %Y %H:%M:%S %Z")
                date_list.append(datetime_obj)
            if "filesize" in k:
                size_list.append(v)
    
    return data, list_name, path_list, date_list, size_list
    
    
def UpdateJson(json_file, data, count, tool_index, list_name, datetime_list, size_list):

    for i in range(count):
        datetime_obj = datetime_list[i]
        data[list_name[tool_index[i]]]['lastModified'] = '{}'.format(*datetime_obj)
        data[list_name[tool_index[i]]]['filesize'] = size_list[i]

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    

# function to query the path from curl, and return status code and datetime
def QueryDependancies(path):

    var = subprocess.Popen(['curl','--retry','3','-D','-','-o','/dev/null','-s',path],shell=True, stdout=subprocess.PIPE)
    out = var.stdout.readlines()
    if "HTTP/1.1 200 OK" in str(out):
        date = [x.decode("utf-8").replace("Last-Modified:", "").strip() for x in out if "Last-Modified:" in str(x)]
        filesize = [x.decode("utf-8").replace("Content-Length:", "").strip() for x in out if "Content-Length:" in str(x)]
        return 0, date, filesize
    else:
        print ("QueryDependancies Failed on {}".format(path))
        sys.exit(1)

# function to check the datetime againt the server, if mismatched return list of path_to_download
def CheckDateTime(date_list,path_list, file_from_folder):
    index=0
    tool_index=[]
    path_to_download=[]
    datetime_list=[]
    size_list=[]
    count = 0
    for path in path_list:
        status, date, size = QueryDependancies(path)

        date_obj = datetime.strptime(*date, "%a, %d %b %Y %H:%M:%S %Z")
        if (status == 0) and (date is not None):
            filesize = file_from_folder.get(os.path.basename(path))
            size = ''.join(map(str, size))

            if (date_obj > date_list[index]) or (str(filesize)!=size):
                if (date_obj > date_list[index]):
                    print ("Last-Modified time mismatched, new version of {} available".format(path))
                else:
                    print ("file size mismatched, download from {}".format(path))
                
                path_to_download.append(path)
                datetime_list.append(date)
                size_list.append(size)
                tool_index.append(index)
                count = count + 1
                
            else:
                pass
        else:
             print ("Unable to query, Network problem")
             sys.exit(1)
        index = index + 1
    
    return count, tool_index, path_to_download, datetime_list, size_list
    

# function to check folder existance
def CheckFolder(path):
    sizelist = dict()
    status = os.path.isdir(path)
    if status is False:
        os.mkdir(path)
        initial = True
        empty_folder = True
    elif len(os.listdir(path)) == 0:
        initial = False
        empty_folder = True
    else:
        initial = False
        empty_folder = False
        size_list = [os.stat(os.path.abspath(path+zipfile)).st_size for zipfile in os.listdir(path)]
        sizelist = dict(zip(os.listdir(path),size_list))
    
    return initial, empty_folder, sizelist
    
def DeleteOldZipped(path_to_download, path):

    filename_list = [os.path.basename(path) for path in path_to_download]
    for file in filename_list:
        if os.path.exists(os.path.abspath(path+file)):
            os.remove(os.path.abspath(path+file))
    
# function to parallel downloand the package from given path
def DownloadDependancies(path):
    error_code = 0
    p = subprocess.Popen(['curl','-A',"\"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64)\"",'--retry','3','--continue-at','-','-O','-L','-s',path],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    print("downloading...")
    p.wait()
    
    out = p.stdout.readlines()
    err = p.stderr.readlines()
    if (len(out)==0) and (len(err)==0):
        error_code = 0
    else:
        error_code = 1

    return error_code

def run_downloader(path, download_folder, max_worker=4):
    os.chdir(download_folder)
    print(f'MESSAGE: Running using Max={max_worker} processes')
    pool = ThreadPool(max_worker)
    results = pool.imap_unordered(DownloadDependancies, path)
    
    if (sum(results) == 0):
        return 0
    else:
        for r in results:
            print(r)
        
        return sum(results)

#main function
if __name__ == '__main__':
    _main()
