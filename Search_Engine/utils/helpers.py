def paginate(results, page, size):
    start = (page-1)*size
    end = page*size
    return results[start:end]
