let getRequest = (url, query) => {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "GET",
            url: url,
            data: query,
        }).done((data) => {
            resolve(data);
        }).fail((jqXHR) => {
            resolve(jqXHR.status);
        })
    })
}

let postRequest = (url, data) => {
    return new Promise((resolve, reject) => {
        $.ajax({
            type: "POST",
            url: url,
            data: data,
            contentType: "application/json"
        }).done((respone) => {
            resolve(respone);
        })
    })
}

export { getRequest, postRequest }
