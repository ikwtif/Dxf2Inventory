from pprint import pprint






def parse_beams_concrete(inventory):
    pprint(inventory)
    for name, item in inventory.items():
        print('name', name)
        del inventory[name]['position_vector']
        for number, parts in item.items():
            if number == 'dimensions':
                pass
            else:
                print('parts', parts)
                print('parttt diameter', parts['diameter'])
                diameter = int(parts['diameter'])
                if diameter in [8, 10, 12, 14, 16,18, 20, 22, 25, 28, 32, 36, 40]:
                    inventory[name][number]['diameter'] = diameter
                else:
                    raise ValueError(f'wapening diameter {diameter} niet correct')
                if 'beugel' in parts.keys():
                    beugel = int(parts['beugel'])
                    if beugel <= 30:
                        item[number]['beugel'] = beugel
                    else:
                        raise ValueError(f'beugelafstand {beugel} te groot')

                lengths = list()
                print(parts)
                for length in parts['lengths']:
                    lengths.append(length[0])
                if 'beugel' not in parts.keys():
                    if len(lengths) == 1:
                        item[number]['plooi'] = 'A'
                    elif len(lengths) == 2:
                        item[number]['plooi'] = 'B'
                    elif len(lengths) == 3:
                        item[number]['plooi'] = 'B'
                    else:
                        raise ValueError(f'too much wapening detected {lengths}')

                else:
                    if len(lengths) == 2:   #TODO what if F ??? -> do this in cad?
                        item[number]['plooi'] = 'E'
    pprint(inventory)

