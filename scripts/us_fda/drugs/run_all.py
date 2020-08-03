import create_enums
import clean_data
import write_mcf


def main():
    print('Starting to create enums....')
    create_enums.main(True)
    print('Enums created- see FDADrugsEnumSchema.mcf')
    print('Starting to clean data....')
    clean_data.main()
    print('Finished cleaning data - see CleanData.csv')
    print('Starting to write data mcf....')
    write_mcf.main()
    print('Finished writing mcf - see FDADrugsFinal.mcf')


if __name__ == '__main__':
    main()
