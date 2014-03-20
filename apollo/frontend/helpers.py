def gen_page_list(page, num_pages, window_size=9):
    start = max(page - (window_size / 2), 1)
    end = min(page - (window_size / 2), num_pages)
    diff = end - start
    if diff < window_size:
        shift = window_size - diff
        if start - shift > 0:
            start -= shift
        else:
            end += shift
    return range(start, end + 1)
