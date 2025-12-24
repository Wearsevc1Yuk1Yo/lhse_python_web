const urls = ['https://ya.ru', 'https://vk.com']

const fetchUrl = async url => {
    try {
        const res = await fetch(url)
    } catch (err) {
        console.log(err)
        return "errrooooorrrr";
    }
};

while (true) {
    console.log(await Promise )
    // console.
    await new Promise(res => setTimeout(res, 5000));
}
