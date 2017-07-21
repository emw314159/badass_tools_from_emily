#
# import useful libraries
#
import pprint as pp
import badass_tools_from_emily.astronomy.solar_noon as sn

#
# main function
#
def main():
    solar_noon = sn.solar_noon(33.1192, -117.0864, 'GMT-0700')
    pp.pprint(solar_noon)

#
# initiate main function
#
if __name__ == "__main__":
    main()
