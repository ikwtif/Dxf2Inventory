import ezdxf
import re
import math
from typing import Any
import logging
from pprint import pprint

logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

file_test = 'testdetail.dxf'
doc = ezdxf.readfile(file_test)
msp = doc.modelspace()


def parse_detail_header(query_mtext):
    """
    :param ezdxf query for Mtext
    :return: nested dictionary {'name': {'header_position':ezdxf vector}}
    """
    logging.info(f'starting parsing detail header for {query_mtext}')
    balken_header = dict()
    try:
        for part in query_mtext:
            search_hoofding = re.search('Wapening\s+(?P<balk_info>B\s*\d+.\d+)', part.text)
            if search_hoofding is not None:
                balken_header[search_hoofding.group('balk_info')] = {'position_vector': part.dxf.insert}
    except Exception as e:
        print(f'exception: {e}')
        pass
    return balken_header



def parse_detail_info(query_text):
    """
    :param query_text: ezdxf query for text
    :return: dictionary with lists of dictionaries
            {'number':[{'position_vector':ezdxf vector, 'wapening':str}, etc], etc}
    """
    #TODO what if wapening/beugels have same number? ADD CHECKS AT WHAT POINT OR DOES IT NOT MATTER?
    logging.info(f'starting parsing detail info for {query_text}')
    balken_detail_info = dict()
    for part in query_text:
        word = part.dxf.text
        # searches info wapening format -> 2%%C16
        # TODO verify and evaluate for accurate numbers -> too many/incorrect according to manufacturing
        try:
            header = re.search('(?P<num>\d+)\s*(?P<wap>\d+%%C\d+)', word, re.UNICODE | re.DOTALL | re.M)
            number = header.group('num')
            wapening = header.group('wap')
            if header is not None:
                if number not in balken_detail_info:
                    balken_detail_info[number] = list()
                balken_detail_info[number].append({'position_vector': part.dxf.align_point,
                                                   'wapening': wapening})

        except AttributeError:
            pass
        except Exception as e:
            print(f'exception: {e}')
            pass
        # searches info wapening - enkel beugels
        # TODO verify and evaluate for accurate numbers -> too many/incorrect according to manufacturing
        try:
            detail_info = re.search('(?P<number>\d+)\s*(?P<beugel>bgl\s*%%C\d+)\s*alle\s*(?P<alle>\d+).*', word, re.UNICODE | re.DOTALL | re.M)
            number = detail_info.group('number')
            beugel = detail_info.group('beugel')
            alle = detail_info.group('alle')
            if detail_info is not None:
                if number not in balken_detail_info:
                    balken_detail_info[number] = list()
                balken_detail_info[number].append({'position_vector': part.dxf.align_point,
                                                   'beugel': beugel,
                                                   'alle': alle})
        except AttributeError:
            pass
        except Exception as e:
            print(f'exception: {e}')
            pass

    return balken_detail_info


logging.info(f'get all mtext from dxf in layer text')
query_mtext_tekstlayer = msp.query('MTEXT [layer=="tekst"]')
balken_header = parse_detail_header(query_mtext_tekstlayer)
logging.info(f'got detail headers for {balken_header}')



logging.info(f'get all text from dxf in layer tekst')
query_text_tekstlayer = msp.query('TEXT [layer=="tekst"]')
balken_detail_info = parse_detail_info(query_text_tekstlayer)
#TODO x axis is the same for everything???
logging.info(f'got detail info for {balken_detail_info}')

#TODO get all length values from details

def parse_detail_lengths(query_text):
    """
    :param query_text: dxf query of text containing length information of a detail
    :return: returns list of lists: [[length_text:str, dxf vector],...]
    """
    #TODO check for closest here to evaluate the different possible rebar bending techniques?
    # or put info inside dxf itself? -> more prone to error? double checks? do both?
    logging.info(f'starting parsing length info for {query_text}')
    balken_detail_lengths = list()
    for part in query_text:
        balken_detail_lengths.append([part.dxf.text, part.dxf.align_point])
    return balken_detail_lengths

logging.info(f'get all length text from dxf in layer 0')
query_text_0layer = msp.query('TEXT [layer=="0"]')
balken_detail_lengths = parse_detail_lengths(query_text_0layer)
logging.info(f'get length info for details {balken_detail_lengths}')

#TODO analyze closest vectors for header and wapening parts //ADD CHECKS FOR ACCURACY BASED ON?
# for wapening en length!!!! -> both in one function?
# start from header and find closest wapening parts

def vector_conditions(self, other, condition):
    """
    determines correct side of the new coordinate position compared to base position of old coordinate
    based on set condition higher or lower or none
    """
    condition = condition.lower()
    if condition == 'higher':
        if self <= other:
            return True
        else:
            return False
    if condition == 'lower':
        if self >= other:
            return True
        else:
            return False
    if condition == 'none':
        return True


def is_close_points_tolerances(self, other: Any, abs_tol: list, conditions:list) -> bool:
    """
    Tolerances for all axis -> list of ints [x_axis_tolerance, y_axis_tolerance, z_axis_tolerance]
        module function: ezdxf.math.is_close_points()
    Conditions for all axis -> list of strings with 'higher' or 'lower' for each axis
        checks for orientation of new point vs base point
    """
    #TODO seems to work -> verify properly -> seems to work as intended)
    #logging.info(f'comparing vectors {self}, {other}')
    other = self.__class__(other)

    check = math.isclose(self.x, other.x, abs_tol=abs_tol[0]) and \
           math.isclose(self.y, other.y, abs_tol=abs_tol[1]) and \
            math.isclose(self.z, other.z, abs_tol=abs_tol[2])
    logging.info(f'check before conditions: {check}')
    if check:
        not_me = [other.x, other.y, other.z]
        for pos, self in enumerate([self.x, self.y, self.z]):
            axis = ['x-axis', 'y-axis', 'z-axis']
            if vector_conditions(self, not_me[pos], conditions[pos]):
                logging.info(f'{axis[pos]} condition accepted -> {conditions[pos]} for self.vector {self} vs self.other {not_me[pos]} '
                             f'with a distance of {not_me[pos]-self}')
                pass
            else:
                check = False
                logging.info(f'{axis[pos]} condition failed -> {conditions[pos]} for self.vector {self} vs self.other {not_me[pos]} '
                               f'with a distance of {not_me[pos]-self}')
                break
    logging.info(f'check after conditions: {check}')
    return check


logging.info(f'start comparing position vectors for header and info')
balken_sorted = dict()
tolerance_header_wapening = [70, 100, 0]
conditions_header_wapening = ['higher', 'lower', 'none']
for balk in balken_header.keys():
    for number_wapening in balken_detail_info.keys():
        for count, item in enumerate(balken_detail_info[number_wapening]):
            if 'wapening' in item.keys():
                it = item['wapening']
            else:
                it = item['beugel']
            logging.info(f'checking for {balk}, number {number_wapening}, item {it}')
            position_header = balken_header[balk]['position_vector']
            position_number_wapening = item['position_vector']
            if is_close_points_tolerances(position_header, position_number_wapening, tolerance_header_wapening, conditions_header_wapening):
                #TODO increase tolerance when nothing is found
                # based on what? how many wapening possible etc -> see algo
                # drop from dict if found
                del balken_detail_info[number_wapening][count]  #TODO deleting used from list good?
                balken_header[balk][number_wapening] = item




#TODO analyze closest vectors for wapening lengths //ADD CHECKS FOR ACCURACY BASED ON?
# relate to header first, then to wapening number -> different tolerance -- just add to tolerance for wapening for x-axis?!
logging.info(f'start comparing position vectors for header/info and lengths')
tolerance_header_lengths = tolerance_header_wapening
tolerance_wapening_lengths = [80, 2, 0]
conditions_header_lengths = conditions_header_wapening
conditions_wapening_lengths = ['higher', 'none', 'none']
print('lengts', balken_detail_lengths)

for balk in balken_header.keys():
    for number in balken_header[balk].keys():
        print('-'*50)
        print('number', number, balk)

        if number != 'position_vector':
            position_wapening = balken_header[balk][number]['position_vector']
            position_header = balken_header[balk]['position_vector']
            lengths_remove = list()
            for count, length in enumerate(balken_detail_lengths):
                print('lengths', balken_detail_lengths)
                print('checking length', length[0])
                position_length = length[1]
                logging.info(f'checking length {length[0]} for {balk} wapening {number}')
                if is_close_points_tolerances(position_header, position_length,
                                              tolerance_header_lengths, conditions_header_lengths) and \
                    is_close_points_tolerances(position_wapening, position_length,
                                               tolerance_wapening_lengths, conditions_wapening_lengths):
                    logging.info(f'found match for {length}')
                    if 'lengths' not in balken_header[balk][number].keys():
                        balken_header[balk][number]['lengths'] = list()
                    logging.info(f'adding {length[0]} to {balk}')
                    lengths_remove.append(balken_detail_lengths[count])
                    balken_header[balk][number]['lengths'].append(length)
                    #TODO something wrong for beugels length checks
                    # deleting from list here causes to skip because count keeps running
            balken_detail_lengths = [i for i in balken_detail_lengths if i not in lengths_remove]
pprint(balken_header)
pprint(balken_detail_lengths)

#TODO DETERMINE HOW FAR IS TO FAR FOR POSITIONS -> USE TEMPLATES FOR DETAILS? prone to errors like everything else
#TODO-ALGO add learning algorithm for better accuracy?
# -> increase x-axis distance when nothing found
# -> limit x-axis distance to next header
#       -> left/right issue!!!
# -> limit y-axis!!!!
#       -> distance to lower header
#       -> up/down issue!!! -> fixed with vector conditions
# => need to check orientation up/down and left/right!!!

#TODO drop things when found

#TODO add condition for distance in dxf if needed and then check and parse it here
'''
#check namen van balken op plan
vectors = list()
for x in m_text:
    print(x.__dict__)
    print(x.dxf.__dict__)
    print(x.doc.__dict__)
    print(x.dxf.insert) #vector mtext
    word = x.text       #text mtext
    print(word)
    searchted = re.search('.+\d+.\d+\s+\d+/\d+\s+((o.b. +\d+.\d+))', word, re.UNICODE | re.DOTALL | re.M)
    print("search", searchted)
    #vectors.append(x.dxf.align_point)
    
    #if word == 'split':
        #print(x.dxf.__dict__)
        #print(x.dxf.align_point.__str__())
        #print(type(x.dxf.align_point))
'''


'''
print(balken)





v1 = balken['1'][0]['vector']
v2 = balken['1'][1]['vector']

tolerance = [0.000000000001, 0.000000000001, 0.000000000001]
print('myfunc', compare(v1, v2, tolerance))
print('ezfunc', ezdxf.math.is_close_points(v1,v2))
print('*'*50)
v_1 = ezdxf.math.Vector()
v_2 = ezdxf.math.Vector(0, 0.000000000001, 0)
print('myfunc', compare(v_1, v_2, tolerance))
print('er func', ezdxf.math.is_close_points(v_1, v_2, 0.00000000000012))

tolerance = [0.000000000001, 0.000000000001, 0.000000000001]
balken_sort = dict()
for balk in balken['1'][0]:
    v1 = balk['vector']
    for number in lengths:
        v2 = number.dxf.align_points
        if compare(v1,v2, abs_tol=tolerance):
            pass

def find_close(v1,V2):
    pass

'''



#TODO figure out how to export to excel
# -> formatting
# -> functions