# 2018-11-21

This is the timing I want to achieve.

    {signal: [
      [ 'clk60 domain',
        {name: 'clk60',         wave: 'p..........'},
      //{name: 'SPRAM.csel',    wave: '10101......'},
        {name: 'SPRAM.addr',    wave: '3x4x5324252', data: ['0', '1', '2', '0', '3', '1', '4', '2']},
        {name: 'SPRAM.datain',  wave: 'xxxxx3x4x5x', data: ['d0\'', 'd1\'', 'd2\'']},
        {name: 'SPRAM.wren',    wave: '0....101010'},
        {name: 'SPRAM.dataout', wave: 'x3x4x5x2x2x', data: ['d0', 'd1', 'd2', 'd3', 'd4']},
      ],
      {},
      [ 'clk30 domain',
        {name: 'clk30',         wave: '10101010101'},
        {name: 'rgb_in',        wave: 'x.3.4.5.2.2', data: ['rgb0', 'rgb1', 'rgb2', 'rgb3']},
       {name: 'pdm_err_in',     wave: 'xx3.4.5.2.2', data: ['d0', 'd1', 'd2', 'd3']},
        {name: 'pdm_err_out',   wave: 'x...3.4.5.2', data: ['d0\'', 'd1\'', 'd2\'']},
        {name: 'LED.rgb_out',   wave: 'x...3.4.5.2', data: ['rgb0', 'rgb1', 'rgb2']},
        {name: 'LED.sclk',      wave: '0....101010'},
      ],
    ]}


# 2018-11-19

This is the timing that doesn't work.

    {signal: [
      {name: 'clk60',         wave: 'p........'},
    //{name: 'SPRAM.csel',    wave: '10101....'},
      {name: 'SPRAM.addr',    wave: '3x4354252', data: ['0', '1', '0', '2', '1', '3', '2', '4']},
      {name: 'SPRAM.datain',  wave: 'xxx3x4x5x', data: ['d0\'', 'd1\'', 'd2\'']},
      {name: 'SPRAM.wren',    wave: '0..101010'},
      {name: 'SPRAM.dataout', wave: 'x3x4x5x2x', data: ['d0', 'd1', 'd2', 'd3']},
      {},
      {name: 'clk30',         wave: '101010101'},
      {name: 'rgb',           wave: '3.4.5.2.2', data: ['rgb0', 'rgb1', 'rgb2', 'rgb3']},
      {name: 'pdm_err',       wave: 'xx3.4.5.2', data: ['d0\'', 'd1\'', 'd2\'']},
      {name: 'pdm_out',       wave: 'xx3.4.5.2', data: ['p0', 'p1', 'p2']},
      {name: 'LED.sclk',      wave: '0..101010'}
    ]}


# 2018-11-18

TNT:

    reg toggle_src;
    reg toggle_cap;
    reg toggle_cap_old;
    wire toggle_change;

    always @(posedge clk_slow)
            toggle_src <= ~toggle_src;

    always @(posedge clk_fast)
    begin
            toggle_cap <= toggle_src;
            toggle_cap_old <= toggle_cap;
            mux_addr <= toggle_change ? rd_addr : rd_addr;
    end

    assign toggle_change = toggle_cap ^ toggle_cap_old;

And the [waveform diagram](https://wavedrom.com/editor.html?%7Bsignal%3A%20%5B%0A%20%20%7Bname%3A%20%27clk_fast%27%2C%20wave%3A%20%27101010101010101010%27%7D%2C%0A%20%20%7Bname%3A%20%27clk_slow%27%2C%20wave%3A%20%270.1.0.1.0.1.0.1.0.%27%7D%2C%0A%20%20%7Bname%3A%20%27toggle_src%27%2C%20wave%3A%20%270.1...0...1...0...%27%7D%2C%0A%20%20%7Bname%3A%20%27toggle_cap%27%2C%20wave%3A%270...1...0...1...0.%27%7D%2C%0A%20%20%7Bname%3A%20%27toggle_cap_old%27%2C%20wave%3A%271.0...1...0...1...%27%7D%2C%0A%20%20%7Bname%3A%20%27toggle_change%27%2C%20wave%3A%271.0.1.0.1.0.1.0.1.%27%7D%2C%0A%20%20%7Bname%3A%20%27rd_addr%27%2C%20wave%3A%20%27x.3...3...3...x...%27%2C%20data%3A%20%5B%27R0%27%2C%20%27R1%27%2C%20%27R2%27%5D%7D%2C%0A%20%20%7Bname%3A%20%27wr_addr%27%2C%20wave%3A%20%27x.4...4...4...x...%27%2C%20data%3A%20%5B%27W0%27%2C%20%27W1%27%2C%20%27W2%27%5D%7D%2C%0A%20%20%7Bname%3A%20%27mux_addr%27%2C%20wave%3A%20%27x...3.4.3.4.3.4.x.%27%2C%20data%3A%5B%27R0%27%2C%27W0%27%2C%27R1%27%2C%27W1%27%2C%27R2%27%2C%27W2%27%5D%7D%0A%5D%7D%0A).
