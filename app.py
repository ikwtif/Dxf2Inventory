import ezdxf
import re
import math
from typing import Any
import logging
from pprint import pprint
from modules import create_excel
from modules import parsing_data

logging.basicConfig(level=logging.CRITICAL, format='%(asctime)s - %(levelname)s - %(message)s')

#file_test = 'testdetail.dxf'
#file_test = 'testfiles/b05.dxf'
#file_test = 'testfiles/b08.dxf'
file_test = 'testfiles/test3.dxf'
doc = ezdxf.readfile(file_test)
msp = doc.modelspace()


def parse_detail_header_mtext(dxf_query, re_search):
    """
    :param dxf_query: ezdxf query for Mtext
    :param re_search: regex expression
    :return: nested dictionary {'name': {'header_position':ezdxf vector}}
    """
    #TODO
    # parsing for headers with "Wapening B0.1/B0.5" or "Wapening B0.1 tem B0.5"
    # parsing for headers with "Detail A-A"
    # handle duplicate errors (same header twice)
    logging.info(f'starting parsing detail header for {dxf_query}')
    header = dict()
    try:
        for part in dxf_query:
            search_hoofding = re.search(re_search, part.text)
            if search_hoofding is not None:
                header[search_hoofding.group('header_info')] = {'position_vector': part.dxf.insert}
    except Exception as e:
        print(f'exception: {e}')
        pass
    return header


def parse_detail_header_text(dxf_query, re_search):
    """
    :param dxf_query: ezdxf query for Mtext
    :param re_search: regex expression
    :return: nested dictionary {'name': {'header_position':ezdxf vector}}
    """
    #TODO
    # parsing for headers with "Wapening B0.1/B0.5" or "Wapening B0.1 tem B0.5"
    # parsing for headers with "Detail A-A"
    logging.info(f'starting parsing detail header for {dxf_query}')
    header = dict()
    try:
        for part in dxf_query:
            search_hoofding = re.search(re_search, part.dxf.text)
            if search_hoofding is not None:
                header[search_hoofding.group('header_info')] = {'position_vector': part.dxf.insert} # dxf.insert for kolommen en detail A-A

    except Exception as e:
        print(f'exception: {e}')
        pass
    return header


def parse_detail_info(dxf_query):
    """
    :param dxf_query: ezdxf query for text
    :return: dictionary with lists of dictionaries
            {'number':[{'position_vector':ezdxf vector, 'wapening':str}, etc], etc}
    """
    #TODO what if wapening/beugels have same number? ADD CHECKS AT WHAT POINT OR DOES IT NOT MATTER?
    logging.info(f'starting parsing detail info for {dxf_query}')
    detail_info = dict()
    for part in dxf_query:
        word = part.dxf.text
        # searches info wapening format -> 2%%C16
        # TODO verify and evaluate for accurate numbers -> too many/incorrect according to manufacturing
        try:
            header = re.search('(?P<number>\d+)\s*(?P<aantal>\d+)%%C(?P<diameter>\d\d+)', word, re.UNICODE | re.DOTALL | re.M)
            number = header.group('number')
            wapening = header.group('aantal')
            diameter = header.group('diameter')
            if header is not None:
                if number not in detail_info:
                    detail_info[number] = list()
                detail_info[number].append({'position_vector': part.dxf.align_point,
                                            'wapening': wapening,
                                            'diameter': diameter
                                            })

        except AttributeError:  #TODO Keep this?
            pass
        except Exception as e:
            print(f'exception: {e}')
            pass
        # searches info wapening - enkel beugels
        # TODO verify and evaluate for accurate numbers -> too many/incorrect according to manufacturing
        try:
            header = re.search('(?P<number>\d+)\s*bgl%%C(?P<diameter>\s*\d+)\s*alle\s*(?P<alle>\d+).*', word, re.UNICODE | re.DOTALL | re.M)
            number = header.group('number')
            diameter = header.group('diameter')
            alle = header.group('alle')
            if header is not None:
                if number not in detail_info:
                    detail_info[number] = list()
                detail_info[number].append({'position_vector': part.dxf.align_point,
                                            'diameter': diameter,
                                            'beugel': alle
                                            })
        except AttributeError:
            pass
        except Exception as e:
            print(f'exception: {e}')
            pass
    return detail_info


def parse_detail_lengths(query_text):
    """
    :param query_text: dxf query of text containing length information of a detail
    :return: returns list of lists: [[length_text:str, dxf vector],...]
    """
    #TODO check for closest here to evaluate the different possible rebar bending techniques?
    # or put info inside dxf itself? -> more prone to error? double checks? do both?
    # sometimes no vector but is None??
    logging.info(f'starting parsing length info for {query_text}')
    detail_lengths = list()
    for part in query_text:
        if part.dxf.align_point is None:
            pass
        else:
            detail_lengths.append([part.dxf.text, part.dxf.align_point])
    return detail_lengths


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


def vector_positions_wapening(items, wapening, tolerance_header_wapening, conditions_header_wapening):
    for item in items.keys():
        for number_wapening in wapening.keys():
            amounts_remove = list()
            amounts = wapening[number_wapening]
            for count, amount in enumerate(amounts):
                #TODO change remove function
                if 'beugel' not in amount.keys():
                    it = amount['wapening']
                else:
                    it = amount['beugel']
                logging.info(f'checking for {item}, number {number_wapening}, amount {it}')
                position_header = items[item]['position_vector']
                position_number_wapening = amount['position_vector']
                if is_close_points_tolerances(position_header, position_number_wapening, tolerance_header_wapening, conditions_header_wapening):
                    #TODO increase tolerance when nothing is found
                    # based on what? how many wapening possible etc -> see algo
                    # drop from dict if found
                    amounts_remove.append(amount)
                    items[item][number_wapening] = amount
                    amounts = [i for i in amounts if i not in amounts_remove]
                    #TODO amounts with removal inside for loop?
            #wapening[number_wapening] = amounts     #assigns new value after removing items found  #TODO FIX this creates dropped wapening for some balken

    return items, wapening  #returning wapening for use with next items


def vector_positions_lengths(items, lengths,
                             tolerance_header_lengths, conditions_header_lengths,
                             tolerance_wapening_lengths, conditions_wapening_lengths_normal):
    for item in items.keys():
        for number in items[item].keys():
            if number != 'position_vector':
                position_wapening = items[item][number]['position_vector']
                position_header = items[item]['position_vector']
                lengths_remove = list()
                for count, length in enumerate(lengths):
                    position_length = length[1]
                    logging.info(f'checking length {length[0]} for {item} wapening {number}')
                    if 'beugel' in items[item][number].keys():
                        #TODO set in a config? -> probably not
                        conditions_wapening_lengths = ['higher', 'lower',
                                                       'none']  # define condition here or somewhere else?
                    else:
                        conditions_wapening_lengths = conditions_wapening_lengths_normal

                    if is_close_points_tolerances(position_header, position_length,
                                                  tolerance_header_lengths, conditions_header_lengths) and \
                            is_close_points_tolerances(position_wapening, position_length,
                                                       tolerance_wapening_lengths, conditions_wapening_lengths):
                        logging.info(f'found match for {length}')
                        if 'lengths' not in items[item][number].keys():
                            items[item][number]['lengths'] = list()
                        logging.info(f'adding {length[0]} to {item}')
                        lengths_remove.append(length)
                        items[item][number]['lengths'].append(length)
                        # deleting from list here causes to skip because count keeps running
                        lengths = [i for i in lengths if i not in lengths_remove]

    return items, lengths   #returning wapening for use with next items


logging.info(f'get all mtext from dxf in layer text')
query_mtext_tekstlayer = msp.query('MTEXT [layer=="tekst"]')
logging.info(f'get all text from dxf in layer tekst')
query_text_tekstlayer = msp.query('TEXT [layer=="tekst"]')

#TODO what if in text vs mtext -> search both?
balken_header = parse_detail_header_mtext(query_mtext_tekstlayer, re_search='Wapening\s+(?P<header_info>B-*\s*\d+.\d+)')
logging.info(f'got detail headers for {balken_header}')
detail_info = parse_detail_info(query_text_tekstlayer)
kolommen_header = parse_detail_header_text(query_text_tekstlayer, re_search='Wapening\s+(?P<header_info>K-*\s*\d+.\d+)')
logging.info(f'got detail headers for {kolommen_header}')
logging.info(f'got detail info for {detail_info}')

logging.info(f'get all length text from dxf in layer 0')
query_text_0layer = msp.query('TEXT [layer=="0"]')
detail_lengths = parse_detail_lengths(query_text_0layer)
logging.info(f'get length info for details {detail_lengths}')
logging.info(f'balken: start comparing position vectors for header and info')

tolerance_header_wapening = [70, 50, 0]
conditions_header_wapening = ['higher', 'lower', 'none']
balken_header, detail_info = vector_positions_wapening(items=balken_header,
                                                       wapening=detail_info,
                                                       tolerance_header_wapening=tolerance_header_wapening,
                                                       conditions_header_wapening=conditions_header_wapening
                                                       )
#TODO analyze closest vectors for wapening lengths //ADD CHECKS FOR ACCURACY BASED ON?
# relate to header first, then to wapening number -> different tolerance -- just add to tolerance for wapening for x-axis?!
logging.info(f'balken: start comparing position vectors for header/info and lengths')
tolerance_header_lengths = tolerance_header_wapening
tolerance_wapening_lengths = [100, 5, 0]
conditions_header_lengths = conditions_header_wapening
conditions_wapening_lengths_normal = ['higher', 'none', 'none']
balken_header, detail_lengths = vector_positions_lengths(items=balken_header,
                                                         lengths=detail_lengths,
                                                         tolerance_header_lengths=tolerance_header_lengths,
                                                         conditions_header_lengths=conditions_header_lengths,
                                                         tolerance_wapening_lengths=tolerance_wapening_lengths,
                                                         conditions_wapening_lengths_normal=conditions_wapening_lengths_normal
                                                         )
#TODO FIX need to fix positioning
# -> some wapening attributed to different numbers //way too wide range was issue, check further...


#TODO DETERMINE HOW FAR IS TO FAR FOR POSITIONS -> USE TEMPLATES FOR DETAILS? prone to errors like everything else
#TODO-ALGO add learning algorithm for better accuracy?
# -> increase x-axis distance when nothing found
# -> limit x-axis distance to next header
#       -> left/right issue!!!
# -> limit y-axis!!!!
#       -> distance to lower header
#       -> up/down issue!!! -> fixed with vector conditions
# => need to check orientation up/down and left/right!!!

#TODO add condition for distance in dxf if needed and then check and parse it here


#check namen van balken op plan
def extract_plan_dimensions_mtext(dxfquery, items, re_search):
    for part in dxfquery:
        word = part.text       #text mtext
        found = re.search(re_search, word, re.UNICODE | re.DOTALL | re.M)
        if found is not None:
        #vectors.append(x.dxf.align_point)
            identifier = found.group('identifier').replace(" ", "")
            dimensions = found.group('dimension').replace(" ", "")
            if '+' in dimensions:
                parse_multiple_dimensions(identifier, dimensions)
            if identifier not in items.keys():
                items[identifier] = {}
            items[identifier]['dimensions'] = dimensions
    return items

# get concrete beams info from groundplan
balken_header = extract_plan_dimensions_mtext(dxfquery=query_mtext_tekstlayer,
                                              items=balken_header,
                                              re_search='(?P<identifier>B\s*\d+.\d+).+(?P<dimension>\d\d+/\d\d+).+(?P<o_b>.o.k..+)'
                                              )

# get steal beams info from groundplan
liggers_header = extract_plan_dimensions_mtext(dxfquery=query_mtext_tekstlayer,
                                               items=dict(),
                                               re_search='(?P<identifier>Li\s*\d+.\d+)\s*(?P<dimension>\w+\s*\d+).+(?P<o_k>.o.k..+)'
                                               )

# get column info from groundplan
#TODO steal and concrete columns BK/SK
kolommen_header = extract_plan_dimensions_mtext(dxfquery=query_mtext_tekstlayer,
                                                items=kolommen_header,
                                                re_search='(?P<identifier>BK\s*.*\d+.\d+)\s*.*(?P<dimension>\d\d+/\d\d+).*'
                                                )
kolommen_header = extract_plan_dimensions_mtext(dxfquery=query_mtext_tekstlayer,
                                                items=kolommen_header,
                                                re_search='(?P<identifier>SK\s*.*\d+.\d+)\s*.*(?P<dimension>\d\d+/\d\d+/\d+).*'
                                                )
pprint(balken_header)
#parsing_data.parse_beams_concrete(balken_header)

#pprint(kolommen_header)

#pprint(liggers_header)
#TODO something wrong with B08 wapening (1) -> because of removing from dict???


#filecreation = create_excel.excelTemplate(balken_header)
#filecreation.create_file()



#TODO figure out how to export to excel
# -> formatting
# -> functions
# -> add length
#   --> how for steel beams
#   --> concrete +6 to lengths good enough?

