library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

------------------------------------------
--entity 
------------------------------------------

entity pre_coder is

  port (
    clk            : in  std_logic;
    rst_n          : in  std_logic;

    -- AXI-Stream slave --
    s_axis_tdata   : in  std_logic_vector(31 downto 0);
    s_axis_tvalid  : in  std_logic;
    s_axis_tready  : out std_logic;
    s_axis_tlast   : in  std_logic;

    -- AXI-Stream master --
    m_axis_tdata   : out std_logic_vector(31 downto 0);
    m_axis_tvalid  : out std_logic;
    m_axis_tready  : in  std_logic;
    m_axis_tlast   : out std_logic
   


  );

end entity;

---------------------------------------------
--architectural behaviour 
---------------------------------------------

architecture rtl of pre_coder is

  type state_type is (IDLE, PROCESSING, OUTPUT_WAIT);
  signal state       : state_type := IDLE;

  
  constant MAX_INDEX_BIT : integer := 31;
  signal input_reg   : std_logic_vector(31 downto 0) := (others => '0');
  signal output_reg  : std_logic_vector(31 downto 0) := (others => '0');
  signal bit_idx     : integer range 0 to 31 := 0;
  signal prev_bit    : std_logic := '0';
  signal toggle      : std_logic := '0';
  
   --------------------------------------
  -- for output controlling
  ---------------------------------------

  signal s_ready_sig : std_logic := '1';
  signal m_valid_sig : std_logic := '0';
  signal m_data_sig  : std_logic_vector(31 downto 0) := (others => '0');
  signal s_last_reg  : std_logic := '0';
  signal m_last_sig  : std_logic := '0';
  

begin

  ---------------------------------------
  -- output port mapping
  ---------------------------------------

  s_axis_tready <= s_ready_sig;
  m_axis_tvalid <= m_valid_sig;
  m_axis_tdata  <= m_data_sig;
  m_axis_tlast  <= m_last_sig;
  

  process(clk)

    ---------------------------------------------------
    -- Variables for calculations in th process block
    ---------------------------------------------------

    variable cur_bit    : std_logic;
    variable a_bit      : std_logic;
    variable b_bit      : std_logic;
    variable temp_out   : std_logic_vector(31 downto 0);
    variable idx        : integer range 0 to 31;

  begin
    if rising_edge(clk) then
      if rst_n = '0' then


      --------------------------------
        -- synchronous reset
      --------------------------------

        state       <= IDLE;
        input_reg   <= (others => '0');
        output_reg  <= (others => '0');
        bit_idx     <= 0;
        prev_bit    <= '0';
        toggle      <= '0';
        s_ready_sig <= '1';
        m_valid_sig <= '0';
        m_data_sig  <= (others => '0');
        m_last_sig  <= '0';
        s_last_reg  <= '0';

      else

        -------------------------------
        --_FSM----
        -------------------------------
        case state is

          -------------------------------
          --IDLE
          --------------------------------

          when IDLE =>
            s_ready_sig <= '1';             --waiting to get the input
            m_valid_sig <= '0';             --no o/p
            if s_axis_tvalid = '1' then     -- get the i/p
              input_reg <= s_axis_tdata;
              output_reg <= (others => '0');
              bit_idx <= 0;
              prev_bit <= '0';
              toggle <= '0';
              s_last_reg <= s_axis_tlast;  --capture the tlast from the sink
              s_ready_sig <= '0';          --start the processing
              state <= PROCESSING;
            end if;

            --------------------------
            --PROCESSING
            --------------------------

          when PROCESSING =>

            temp_out := output_reg;        --initialize the temp_out
            idx := bit_idx; 

           ---------------------------------
           --GMSK PRECODER LOGIC BIT_BY_BIT
           --------------------------------- 

            cur_bit := input_reg(idx);
            b_bit := cur_bit xor prev_bit;
            a_bit := b_bit xor toggle;
            temp_out(idx) := a_bit;

           --storing the output to the temporary list

            output_reg <= temp_out;
            prev_bit <= cur_bit;          --update and toggle
            toggle <= not toggle;


            ------------------------------------------
            -- LAST BIT HANDELLING OF THE LAST WORD
            ------------------------------------------

            if idx = MAX_INDEX_BIT then
              m_data_sig <= temp_out;     --o/p the register
              m_valid_sig <= '1';         --wait for sink to response
              m_last_sig <= s_last_reg;   --use to assert m_axis_tlast at the last o/p
              bit_idx <= 0;
              state <= OUTPUT_WAIT;
            else
              bit_idx <= idx + 1;
              
            end if;

            --------------------------------
            --WAIT FOR THE OUTPUT
            --------------------------------

          when OUTPUT_WAIT =>

            if  m_axis_tready = '1' then  --o/p handshake
              m_valid_sig <= '0';
              s_ready_sig <= '1';
              state <= IDLE;
            end if;

          when others =>
            state <= IDLE;

        end case;
      end if;
    end if;
  end process;
end architecture;