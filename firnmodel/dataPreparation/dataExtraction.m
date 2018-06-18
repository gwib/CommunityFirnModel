%%
% coordinates of profile 1 (flade isblink 46density)
coord1 = [81.25 -15.7];
%coordinates of profile 2 (B26)
coord2 = [77.25 -49];

% coordinates of profile 3
coord3 = [77.45 -51.06];


% vector of latitudes
lats = [81.28 77.25 77.45];
lons = [-15.7 -49 -51.06];

% find coordinates in info file and indices for profiles
% load info file
info = load('./weatherInput/Infodata.mat');

%round(X,N)
info_lon = round(info.lon, 2);
info_lat = round(info.lat, 2);

indices = zeros(numel(lats));
% find coordinates in info file and indices for profiles
% for i = 1:numel(lats)
%     indices(i) = find(info_lat == lats(i) & info_lon(i)==lon(i));
% end
% 
% function y = myIntegrand(x)
% y = sin(x).^3;
% end

%disp(indices)


% useful for later: find value closest to pH
% [~, idx] = min(abs(pH - 4.756));

years = 1980:2016;

temp = containers.Map;
smb = containers.Map;

for i=1:numel(years)
    y = num2str(years(i));
    ystr = strcat('./weatherInput/HH2018_',y,'.mat');
    yearFile = load(ystr);
    temp(y) = yearFile.Temp;
    smb(y) = yearFile.smb;
end

siteNames = {'site1', 'site2', 'site3'};
siteIndex = containers.Map;
for j=1:numel(siteNames)
    siteIndex(char(siteNames(j)))  = findIndex(info_lat, info_lon, lats(j), lons(j));
end

%%
siteTemps = containers.Map(siteNames, cellfun(@(x) zeros(13,numel(years)),siteNames,'UniformOutput',false));
siteSMBs = containers.Map(siteNames, cellfun(@(x) zeros(13,numel(years)),siteNames,'UniformOutput',false));



% for name=siteNames
%     siteName = char(name);
%     siteTemps(siteName) = zeros(numel(years), 12);
%     siteSMBs(siteName) = zeros(numel(years), 12);
% end
%%
for year=years
    y = num2str(year);
    tempYear = temp(y);
    smbYear = smb(y);
    yearIndex = numel(years) - (max(years) - year);
    disp(yearIndex)
    for name=siteNames
        siteName = char(name);
        siteI = siteIndex(siteName);
        siteTemp = siteTemps(siteName);
        siteSMB = siteSMBs(siteName);
        
        
        siteTemp(:,yearIndex) = [year tempYear(siteI,:)];
        siteSMB(:,yearIndex) = [year smbYear(siteI,:)];
        
        siteTemps(siteName) = siteTemp;
        siteSMBs(siteName) = siteSMB;
        
    end
end

%% write csv
for site=siteNames
    s = char(site);
    folder = '../CFM_main/extractedData/';
    tempFileName = strcat(folder,'temp_',s,'.dat');
    smbFileName = strcat(folder,'smb_',s,'.dat');
    csvwrite(tempFileName,siteTemps(s));
    csvwrite(smbFileName,siteSMBs(s));
end




function index = findIndex(info_lat, info_lon, inLat, inLon)
    idx = find(info_lat == inLat & info_lon == inLon);
    m=1;
    while isempty(idx)
        idx= find((info_lat < inLat+0.02*m & info_lat > inLat-0.02*m) & (info_lon > inLon-0.02*m &info_lon < inLon+0.02*m));
        m = m+2;
    end
    if numel(idx) > 1
        idx = idx(1);
    end
    index = idx;
end