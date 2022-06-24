import copy


def xmean(field, j, i):
    # nrows = len(field)
    ncols = len(field[0])
    minval = 0.0
    minpos = i
    maxpos = i
    maxval = 0.0

    while minpos >= 0 and field[j][minpos] == -1:
        minpos -= 1

    if minpos >= 0:
        minval = field[j][minpos]

    minpos += 1

    while maxpos < ncols and field[j][maxpos] == -1:
        maxpos += 1

    if maxpos < ncols:
        maxval = field[j][maxpos]

    maxpos -= 1

    num = maxpos - minpos + 1

    if maxval > minval:
        tval = minval + ((maxval - minval) / (num + 1)) * (i + 1 - minpos)
    else:
        tval = maxval + (abs(maxval - minval) / (num + 1)) * abs(i - 1 - maxpos)

    return {'t': tval, 'w': num}


def ymean(field, j, i):
    nrows = len(field)
    # ncols = len(field[0])
    minval = 0.0
    minpos = j
    maxpos = j
    maxval = 0.0

    while minpos >= 0 and field[minpos][i] == -1:
        minpos -= 1

    if minpos >= 0:
        minval = field[minpos][i]

    minpos += 1

    while maxpos < nrows and field[maxpos][i] == -1:
        maxpos += 1

    if maxpos < nrows:
        maxval = field[maxpos][i]

    maxpos -= 1

    num = maxpos - minpos + 1

    if maxval > minval:
        tval = minval + ((maxval - minval) / (num + 1)) * (j + 1 - minpos)
    else:
        tval = maxval + (abs(maxval - minval) / (num + 1)) * abs(j - 1 - maxpos)

    return {'t': tval, 'w': num}


def dpmean(field, j, i):
    nrows = len(field)
    ncols = len(field[0])

    minval = 0.0
    minposy = j
    maxposy = j
    minposx = i
    maxposx = i
    maxval = 0.0

    countb = 0
    while minposx >= 0 and minposy >= 0 and field[minposy][minposx] == -1:
        countb += 1
        minposx -= 1
        minposy -= 1

    if minposx >= 0 and minposy >= 0:
        minval = field[minposy][minposx]

    minposx += 1
    minposy += 1
    countb -= 1

    countf = 0
    while maxposx < ncols and maxposy < nrows and field[maxposy][maxposx] == -1:
        countf += 1
        maxposx += 1
        maxposy += 1

    if maxposx < ncols and maxposy < nrows:
        maxval = field[maxposy][maxposx]

    maxposx -= 1
    maxposy -= 1
    countf -= 1

    count = countb + countf + 1

    if maxval > minval:
        tval = minval + ((maxval - minval) / (count + 1)) * (countb + 1)

    else:
        tval = maxval + (abs(maxval - minval) / (count + 1)) * (countf + 1)

    return {'t': tval, 'w': count}


def dsmean(field, j, i):
    nrows = len(field)
    ncols = len(field[0])

    minval = 0.0
    minposy = j
    maxposy = j
    minposx = i
    maxposx = i
    maxval = 0.0

    countb = 0
    while minposx >= 0 and minposy < nrows and field[minposy][minposx] == -1:
        countb += 1
        minposx -= 1
        minposy += 1

    if minposx >= 0 and minposy < nrows:
        minval = field[minposy][minposx]

    minposx += 1
    minposy -= 1
    countb -= 1

    countf = 0
    while maxposx < ncols and maxposy >= 0 and field[maxposy][maxposx] == -1:
        countf += 1
        maxposx += 1
        maxposy -= 1

    if 0 <= maxposy < nrows and maxposx < ncols:
        maxval = field[maxposy][maxposx]

    maxposx -= 1
    maxposy += 1
    countf -= 1

    count = countb + countf + 1

    if maxval > minval:
        tval = minval + ((maxval - minval) / (count + 1)) * (countb + 1)
    else:
        tval = maxval + (abs(maxval - minval) / (count + 1)) * (countf + 1)

    return {'t': tval, 'w': count}


def add_recursive(field, border_list, y, x):
    nrows = len(field)
    ncols = len(field[0])

    # if (y * ncols + x) in border_list:
    #    return True

    # check if is part of the border_list cells
    is_border_list = False
    for i in range(-1, 2, 2):

        if y * ncols + (x + i) in border_list:
            is_border_list = True
        if (y + i) * ncols + x in border_list:
            is_border_list = True

    if is_border_list:

        border_list[y * ncols + x] = 1

        for i in range(-1, 2, 2):

            if 0 <= x + i < ncols:
                if field[y][x + i] == -1:
                    if y * ncols + x + i not in border_list:
                        add_recursive(field, border_list, y, x + i)
            if 0 <= y + i < nrows:
                if field[y + i][x] == -1:
                    if (y + i) * ncols + x not in border_list:
                        add_recursive(field, border_list, y + i, x)


def get_outside(field):
    nrows = len(field)
    ncols = len(field[0])

    border_list = {}

    # get border_list's empty cell
    for j in range(1, nrows - 1):
        if field[j][0] == -1:
            border_list[j * ncols + 0] = 1
            add_recursive(field, border_list, j, 0)

        if field[j][ncols - 1] == -1:
            border_list[j * ncols + ncols - 1] = 1
            add_recursive(field, border_list, j, ncols - 1)

    for i in range(0, ncols):
        if field[0][i] == -1:
            border_list[i] = 1
            add_recursive(field, border_list, 0, i)
        if field[nrows - 1][i] == -1:
            border_list[(nrows - 1) * ncols + i] = 1
            add_recursive(field, border_list, nrows - 1, i)

    return border_list


def get_outside_i(field):
    nrows = len(field)
    ncols = len(field[0])

    candidates = {}
    for y in range(0, nrows):
        for x in range(0, ncols):
            if field[y][x] == -1:
                try:
                    candidates[y][x] = 1
                except KeyError:
                    candidates[y] = {}
                    candidates[y][x] = 1

    border = {}
    border_modified = True

    while border_modified:
        border_modified = False
        for y, row in candidates.items():
            for x, v in row.items():
                is_border = False

                if v == 1: 
                    if x == 0 or y == 0 or x == ncols - 1 or y == nrows - 1:
                        is_border = True
                    else:
                        for i in range(-1, 2, 2):
                            if 0 <= x + i < ncols: 
                                if y * ncols + x + i in border: 
                                    is_border = True
                        
                            if 0 <= y + i < nrows: 
                                if (y + i) * ncols + x in border: 
                                    is_border = True
                    
                    if is_border: 
                        border[y * ncols + x] = 1
                        border_modified = True
                        candidates[y][x] = 0
                    
    return border


def fill_holes(field):
    fnext = copy.deepcopy(field)
    border = get_outside_i(field)

    n_h = len(field)
    n_w = len(field[0])

    for j in range(0, n_h):
        for i in range(0, n_w):
            if fnext[j][i] == -1 and j * n_w + i not in border:
                contrib = []
                tweight = 0.0

                res = xmean(fnext, j, i)

                if res['t'] > 0:
                    contrib.append(res['t'] / res['w'])
                    tweight += 1.0 / res['w']

                res = ymean(fnext, j, i)

                if res["t"] > 0:
                    contrib.append(res["t"] / res["w"])
                    tweight += 1.0 / res['w']

                res = dpmean(fnext, j, i)

                if res['t'] > 0:
                    contrib.append(res['t'] / res['w'])
                    tweight += 1.0 / res['w']

                res = dsmean(fnext, j, i)

                if res['t'] > 0:
                    contrib.append(res['t'] / res['w'])
                    tweight += 1.0 / res['w']

                if len(contrib) > 0:
                    field[j][i] = sum(contrib) / tweight
