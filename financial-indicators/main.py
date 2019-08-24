import logging
import os
import sys

import bcb_api
import excel_writer
import indicators_expander
import utils


# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create stream handler
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] [%(module)s] [%(funcName)s] [%(lineno)d] [%(message)s]'
)
sh.setFormatter(formatter)
logger.addHandler(sh)

logging_path = utils.create_log_path()
if logging_path is not None:
    # Create file handler
    fh = logging.FileHandler(os.path.join(logging_path, 'financial-indicators.log'), 'w')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)


def handle_exception(exc_type, exc_value, exc_traceback):
    """ Function designed to override the sys.excepthook function, which
    is the last function called before an uncaught exception is raised,
    and log the exception information before quitting.
    """
    logger.critical(
        "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
    )


@utils.log_func_time(logger, 20)
def main():
    logger.info('Starting program...')

    working_indicators = (
        11,
        12,
        226,
        433,
    )

    api = bcb_api.FinancialIndicatorsApi()
    expander = indicators_expander.IndicatorExpander()
    workbook = excel_writer.IndicatorsWorkbook(
        path_to_file=utils.bundle_dir,
        filename='financial-indicators.xlsx'
    )

    need_update = False  # was any indicator updated?
    for indicator_code in working_indicators:
        wb_last_date = workbook.get_indicator_last_date(indicator_code)
        api.set_indicators_records({indicator_code: (wb_last_date, None)})
        api_last_date = api.get_latest_date(indicator_code)

        if wb_last_date == api_last_date:
            logger.info(f'indicator code {indicator_code} is up-to-date')
            continue
        else:
            logger.info(f'Updating indicator code {indicator_code}')
            need_update = True
            expanded_indicator = expander.get_expanded_indicators(
                indicator_code, api[indicator_code]
            )
            workbook.write_records(indicator_code,
                                   expanded_indicator,
                                   api_last_date)

    if need_update:
        workbook.save()


if __name__ == '__main__':
    sys.excepthook = handle_exception
    main()
