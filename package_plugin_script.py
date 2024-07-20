import subprocess
import os.path
import json

config_path = "./config.json"

f = open(config_path)
data = json.load(f)

if data:
    success_packages = []
    failed_packages = []
    
    #Get basic configuration
    package_destination = data["destination_path"]
    uat_dir = data["uat_dir"]
    engine_parent_dir = data["engine_parent_dir"]
    version_dictionary = data["plugin_versions"]
    
    for plugin_version in version_dictionary:
        plugin_path = plugin_version["plugin_path"]
        engine_versions = plugin_version["engine_versions"]
        #Check if plugin is present
        if os.path.isfile(plugin_path):
                   
            #Check if specific platform(s) have been provided
            if "platforms" not in plugin_version:
                platforms = [data["no_platform_provided_dir_name"]]
            else:
                platforms = plugin_version["platforms"]
            
            print("Starting {plugin_v}".format(plugin_v = plugin_path))
                
            #Group platforms if not forcing seperate builds
            if not(data["build_seperate_platform_versions"]):
                platformstring = ""
                for plugin_platform in platforms:
                    platformstring += plugin_platform
                    platformstring += ","
                platforms = [platformstring[:-1]] #remove last ","
            
            for current_platform in platforms:
                print("Platform: {platform}".format(platform = current_platform))
                for engine_version in engine_versions:
                    destination_path = package_destination.format(package_version = engine_version, platform = current_platform.replace(",","_"))
                    
                    #Handle skipping already packaged builds
                    if data["skip_already_packaged"] and os.path.isdir(destination_path):
                        success_packages.append("Already Packaged: {plugin_v} for {engine_v} for {platform}".format(engine_v = engine_version, plugin_v = plugin_path, platform = current_platform))
                        continue;
                    
                    #Check if engine is present
                    tool_path = engine_parent_dir + uat_dir.format(version = engine_version)
                    if os.path.isfile(tool_path):
                        print("Packaging: {engine_v}".format(engine_v = engine_version))
                        
                        #Create command for packaging plugin
                        cmd = "{tool_p} BuildPlugin -Plugin={plugin_v} -Package={destination_p} ".format(tool_p = tool_path, plugin_v = plugin_path, destination_p = destination_path)
                        
                        #If specific platform(s) have been provided, add target platform(s)
                        if current_platform != data["no_platform_provided_dir_name"]:
                            cmd += "-TargetPlatform={platform} ".format(platform = current_platform)
                        
                        #Add default arguments provided
                        if "default_args" in data:
                            for default_arg in data["default_args"]:
                                cmd += "-"
                                cmd += default_arg
                                cmd += " "
                        
                        #Add plugin specific arguments provided
                        if "args" in plugin_version:
                            for arg in plugin_version["args"]:
                                cmd += "-"
                                cmd += arg
                                cmd += " "
                        
                        #Capture stdout if possible
                        if data["print_stdout"]:
                            p = subprocess.run(cmd, stderr = subprocess.PIPE)
                        else:
                            p = subprocess.run(cmd, stderr = subprocess.PIPE, stdout = subprocess.PIPE)
                        
                        if p.returncode > 0:
                            #Fail
                            if p.stdout:
                                errordetails = p.stdout.splitlines()[-data["error_lines_to_print"]:]
                            else:
                                errordetails = p.returncode
                            print("Failed packaging: {engine_v} with Exitcode: {exitcode}".format(engine_v = engine_version, exitcode = p.returncode))
                            print("Error Details: \n {err}".format(err = errordetails))
                            failed_packages.append("Failed: {plugin_v} for {engine_v} Reason: {err}".format(plugin_v = plugin_path, engine_v = engine_version, err = errordetails))
                        else: 
                            #Success
                            print("Successfully packaged: {engine_v}".format(engine_v = engine_version))
                            success_packages.append("Success: {plugin_v} for {engine_v} for {platform}".format(engine_v = engine_version, plugin_v = plugin_path, platform = current_platform))
                    else:
                        #Fail : Missing Engine
                        print("Engine: {engine_v} is missing. Skipping...".format(engine_v = engine_version))
                        failed_packages.append("Failed: {plugin_v} for {engine_v} Reason: Missing engine".format(plugin_v = plugin_path, engine_v = engine_version))
        else:
            #Fail : Missing Plugin
            print("Plugin: {plugin_v} is missing. Skipping...".format(plugin_v = plugin_path))
            for engine_version in engine_versions:
                failed_packages.append("Failed: {plugin_v} for {engine_v} Reason: Missing plugin".format(plugin_v = plugin_path, engine_v = engine_version))
    
    for success in success_packages:
        print(success)
    
    for failed in failed_packages:
        print(failed)
    
    if len(failed_packages) > 0:
        print("Process finished with errors")
    else:
        print("Process successfully finished")
else:
   print("Failed to load {config}".format(config = config_path))     
   print("Process finished with errors")