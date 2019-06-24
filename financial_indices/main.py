import logging

import bcb_api
import excel_writer
import indices_expander


logger = logging.getLogger(__name__)


def main():
    api = bcb_api.FinancialIndicesApi()
    expander = indices_expander.IndicesExpander()
    workbook = excel_writer.IndicesWorkbook()

    working_indices = (
        11,
        12,
        226,
        433,
    )

    for indices_code in working_indices:
        wb_last_date = workbook.get_last_indices_date(indices_code)
        api.set_indices_records({indices_code: (wb_last_date, None)})
        api_last_date = api.get_latest_date(indices_code)

        if wb_last_date == api_last_date:
            continue

        expander.set_expanded_indices(indices_code, api[indices_code])
        workbook.write_records(indices_code, expander[indices_code], api_last_date)

    workbook.save()


if __name__ == '__main__':
    import time

    start = time.perf_counter()

    main()

    end = time.perf_counter()

    print(end - start)
