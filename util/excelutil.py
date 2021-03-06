def getStockDataBySheet(excelProxy, sheet):
    #from easyExcel import EasyExcel
    #import os,sys
    #root = os.path.abspath(os.path.dirname(sys.argv[0]))
    #print '*******root path*****',root
    #path = root +'\\test.xls'
    #excelProxy = EasyExcel(path)
    #print excelProxy.getSheets()
    #sheet = "2"
    print "***********Excel Sheet******", sheet
    line = 2
    while True:
        if excelProxy.getCell(sheet, line, 1) is None:
            break
        else:
            line = line + 1
    print "***********Overall trading count******", line - 2

    content = excelProxy.getRange(sheet, 2, 1, line - 1, 5)
    #print content
    sum = 0
    revenue = 0
    #trading history
    directory = dict()

    from trading import Trading

    for line in content:
        #print line
        code = line[1]
        #print code
        volume = int(int(line[2]) * float(line[3]))
        #print type(volume)
        #print volume
        tempRev = 0
        if (line[4] != None):
            tempRev = int(line[4])
            revenue += tempRev
        trade = Trading(code, 1, abs(volume), tempRev)
        if code not in directory:
            #trade = Trading(code,1,abs(volume),0)
            #directory[code] = abs(volume)
            directory[code] = trade
        else:
            temp = directory[code]
            #print '**********'+str(trade.volume)
            #print '**********'+str(temp.volume)
            trade.add(temp.volume, temp.revenue)
            #trade.count += 1
            #trade.volume += abs(volume)
            #temp = directory[code]
            #directory[code] = abs(volume)+temp
            directory[code] = trade
        #print volume
        sum += abs(volume)

    #print sum
    #print revenue
    #directory["total"] = sum

    #print directory
    #for trade in directory.values():
    #print trade

    #print len(directory)
    print "************Sum Column*********", sum
    print "************revenue************", revenue

    #directory['sum'] = sum
    #close the Excel file
    #excelProxy.close()
    return directory


if __name__ == '__main__':
    pass
	

			

