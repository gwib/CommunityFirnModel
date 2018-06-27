function [lat,lon] = extractData2(inIndex)
%EXTRACTDATA2 Summary of this function goes here
%   Detailed explanation goes here
icesatyears = 2003:2008;

info = load('../dataPreparation/weatherInput/Infodata.mat');

%round(X,N)
info_lon = round(info.lon, 2);
info_lat = round(info.lat, 2);

temp = containers.Map;
smb = containers.Map;

for y= icesatyears
    ystr = num2str(y);
    yfolder = strcat('../dataPreparation/weatherInput/HH2018_',ystr,'.mat');
    yearFile = load(yfolder);
    temp(ystr) = yearFile.Temp;
    smb(ystr) = yearFile.smb;
end

temps = zeros(13,numel(years));
smbs = zeros(13,numel(years));

for year=icesatyears
    y = num2str(year);
    tempYear = temp(y);
    smbYear = smb(y);
    yearIndex = numel(icesatyears) - (max(icesatyears) - year);

    temps(:,yearIndex) = [year tempYear(inIndex,:)];
    smbs(:,yearIndex) = [year smbYear(inIndex,:)];
end

idx = int2str(inIndex);
folder = '../CFM_main/autoRunInput/';
tempFileName = strcat(folder,'temp_',idx,'.csv');
smbFileName = strcat(folder,'smb_',idx,'.csv');
csvwrite(tempFileName,temps);
csvwrite(smbFileName,smbs);

lat = info_lat(inIndex);
lon = info_lon(inIndex);
end

